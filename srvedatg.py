import logging

from edlinkn8 import Everdrive
from edlinkn8 import NesRom
from stackrabbit import get_move

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

TIMELINE_10_HZ = "X....."

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
    def __init__(self, state: bytearray):
        self.state = state

    def get_sr_payload(self):
        return (
            f"{self.playfield}|"
            f"{self.levelNumber}|"
            f"{self.lines}|"
            f"{self.currentPiece}|"
            f"{self.nextPiece}|"
            f"{TIMELINE_10_HZ}|"
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
        return self.state[202]

    @property
    def currentPiece(self):
        return ORIENTATION_TO_SR[self.state[200]]

    @property
    def nextPiece(self):
        return ORIENTATION_TO_SR[self.state[201]]


def main():
    logger.info("Launching custom version of tetrisgym...")
    everdrive = Everdrive()
    everdrive.load_game(NesRom.from_file("TetrisGYM/tetris.nes"))

    while True:
        try:
            if not (data := everdrive.receive_data(205)):
                continue
            logger.debug(f"Received {len(data)} bytes!")
            state = PlayfieldState(data)
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
