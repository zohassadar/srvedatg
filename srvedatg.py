import logging

from edlinkn8 import Everdrive
from edlinkn8 import NesRom
from stackrabbit import get_move

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def main():
    logger.info("Launching custom version of tetrisgym...")
    everdrive = Everdrive()
    everdrive.load_game(NesRom.from_file('TetrisGYM/tetris.nes'))

    while True:
        logger.info(f'Reading playfield state')
        if data := everdrive.receive_data(205):
            logger.info(f'Received {len(data)}!')

if __name__ == "__main__":
    main()
