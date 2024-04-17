import argparse
import logging
import os
import subprocess
import sys

from edlinkn8 import Everdrive
from edlinkn8 import NesRom
from stackrabbit import get_move

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

GAME_DATA_LEN = 205

TIMELINE_8_HZ = "X......"

# spawn orientation to stackrabbit piece identifier
ORIENTATION_TO_SR = {
    18: 0,  # I
    10: 1,  # 0
    14: 2,  # L
    7: 3,  # J
    2: 4,  # T
    11: 5,  # S
    8: 6,  # Z
}

# sr id + sr offset to orientation
SR_OFFSET_TO_ORIENTATION = {
    (0, 0): 18,  # I vert
    (0, 1): 17,  # I horiz
    (1, 0): 10,  # O
    (2, 0): 14,  # L down
    (2, 1): 15,  # L left
    (2, 2): 16,  # L up
    (2, 3): 13,  # L right
    (3, 0): 7,  # J down
    (3, 1): 4,  # J left
    (3, 2): 5,  # J up
    (3, 3): 6,  # J right
    (4, 0): 2,  # T down
    (4, 1): 3,  # T left
    (4, 2): 0,  # T up
    (4, 3): 1,  # T right
    (5, 0): 11,  # S horiz
    (5, 1): 12,  # S vert
    (6, 0): 8,  # S horiz
    (6, 1): 9,  # S vert
}


class PlayfieldState:
    def __init__(self, state: bytearray, level: int | None, hertz: str | None):
        self.level = level
        self.hertz = hertz if hertz else TIMELINE_8_HZ
        self.state = state

    def get_sr_payload(self):
        return (
            f"{self.playfield}|"
            f"{self.levelNumber}|"
            f"{self.lines}|"
            f"{self.currentPiece}|"
            f"{self.nextPiece}|"
            f"{self.hertz}|"
        )

    @property
    def playfield(self):
        return "".join("0" if b & 0x80 else "1" for b in self.state[:200])

    @property
    def lines(self):
        lo = self.state[203]
        hi = self.state[204]
        return (hi * 100) + ((lo >> 4) * 10) + (lo & 0xF)

    @property
    def levelNumber(self):
        if self.level is not None:
            return self.level
        return self.state[202]

    @property
    def currentPiece(self):
        return ORIENTATION_TO_SR[self.state[200]]

    @property
    def nextPiece(self):
        return ORIENTATION_TO_SR[self.state[201]]

def build_gym(*flags: tuple[str]):
    args = ['node', 'build.js', '-S']
    if flags:
        args.append('--')
        args.extend(flags)
    logger.info(f"Building TetrisGYM with command: {' '.join(args)}")
    curdir = os.path.dirname(__file__)
    os.chdir(os.path.join(curdir, 'TetrisGYM'))
    build = subprocess.Popen(args, stdout=subprocess.PIPE)
    os.chdir(curdir)
    result, error = build.communicate()
    result = result.decode()
    if "Error:" not in result:
        logger.info(result)
        return
    
    logger.critical(f"Unable to build Gym: Error: {result.split('Error:')[1]}")
    sys.exit(1)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--level', type=int, help='level override', default=None)
    parser.add_argument('-f', '--frames', type=int, help='frames to display.  default 10')
    parser.add_argument('-s', '--showsooner', action="store_true", help='show the move as soon as possible')
    parser.add_argument('-H', '--hertz', help='stackrabbit timeline', default=None)
    args = parser.parse_args()
    flags = []
    if args.frames:
        flags.extend(['-D', f'SRVEDATG_DISPLAY_FRAMES={args.frames}'])
    if args.showsooner:
        flags.extend(['-D', 'SRVEDATG_SHOW_SOONER=1'])
    return flags, args.level, args.hertz


def empty_buffer(everdrive: Everdrive):
    i = 0
    while True:
        if not everdrive.receive_data(1):
            break
        i+=1
    logger.info(f"Emptied the buffer of {i} bytes")


def main():
    flags, level, hertz = get_args()
    build_gym(*flags)
    logger.info("Launching TetrisGYM...")
    everdrive = Everdrive()
    everdrive.load_game(NesRom.from_file("TetrisGYM/tetris.nes"))

    while True:
        try:
            if not (data := everdrive.receive_data(GAME_DATA_LEN)):
                continue
            if (buffer_len := len(data)) != GAME_DATA_LEN:
                logger.error(f"Received {buffer_len} bytes.  Expected {GAME_DATA_LEN}")
                empty_buffer(everdrive)
            logger.debug(f"Received {len(data)} bytes!")
            state = PlayfieldState(data, level, hertz)
            best_move = get_move(state.get_sr_payload())
            logger.debug(f"Stackrabbit says to: {best_move}")
            offset, x, y = eval(best_move)
            payload = bytearray(3)
            if x > 5 or y > 19 or offset > 3:
                logger.error(f"No valid move from stackrabbit")
                continue
            payload[0] = SR_OFFSET_TO_ORIENTATION[(state.currentPiece, offset)]
            payload[1] = y
            payload[2] = 5 + x
            everdrive.write_fifo(payload)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
