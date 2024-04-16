# StackRabbit via Everdrive and TetrisGYM


## Install

```
git submodule update --init

python -m venv .venv
echo "*" > .venv/.gitignore
. .venv/bin/activate

pip install pyserial python-edlinkn8/

cd StackRabbit/
python setup.py install

cd TetrisGYM/
node build.js -S

```

