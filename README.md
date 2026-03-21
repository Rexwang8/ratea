## Ratea MK2

Note: Please use the [develop](https://github.com/Rexwang8/ratea/tree/develop) branch if you want the latest, potentially broken features. Please use [main](https://github.com/Rexwang8/ratea/tree/main) branch otherwise.

Different from mk1

Attempts to track tea purchases and reviews. Can be used to generate charts.

Python 3.10+ (sorry)


## Installation

Install the required dependencies using:

```bash
pip install -r requirements.txt
```



## Run

Run with:

```

cd ratea
python src/main.py

```
*not `python ratea/src/main.py` for now, will fix later

Let me know if you can't start the application or if something displays really weirdly.

Only tested on windows 10.

Configs in `./ratea/src/config.py` 

Set UI_SCALE to 2 for 4k monitor, to 1 or 1.5 for normal monitors.


## Charting

Can also make some charts, mainly running off of pyplot.

Example:

![Example](./cpg_over_time_example.png)




Hobby project started late 2025

If you see any problems you should fix it and PR it. 

If you are complaining, inshallah they will find you.