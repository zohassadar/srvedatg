# StackRabbit via Everdrive and TetrisGYM

Briefly displays where StackRabbit would have moved based on a 10hz timeline using the Everdrive N8 Pro's USB connection

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

## Play

Have everdrive connected and in menu

```
python srvedatg.py

```


