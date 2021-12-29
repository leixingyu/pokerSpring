<div align="center">
<h1 align="center">Poker Spring (Poker Rig for Card Spring)</h1>

  <p align="center">
    A control rig that is made for manipulating a deck of poker to create spring
effect, ready for animation use.
    <br />
    <a href="https://youtu.be/AJneUcGDRl0">Full Demo</a>
  </p>
</div>

## About The Project

<div align="left">
<img src="https://i.imgur.com/O19dFu1.jpg" alt="poker-title" height="65%" width="65%"/>
</div>


## Getting Started

1. Unzip the **poker-spring** package under
`%USERPROFILE%/Documents/maya/[current maya version]/scripts/`
or a custom directory under `PYTHONPATH` env variable. 


2. Rename the package to something like `pokerSpring`


3. Launch through script editor:
    ```python
    from pokerSpring import pokerUI
    pokerUI.show()
    ```

## Usage

The current version of the tool requires a maya file already being setup, it contains the
necessary control curves to guide the cards, which can be found in 
the [example folder](https://github.com/leixingyu/poker-spring/tree/master/example).

<div align="left">
    <img src="https://i.imgur.com/AUzqbrW.gif" alt="initialize" height="75%" width="75%"/>
    <p><b>Initialize deck starting look, adjust card spring parameter using slider</b></p>
</div>

<br>

<div align="left">
    <img src="https://i.imgur.com/hw5ipoC.gif" alt="shuffle" height="75%" width="75%"/>
    <p><b>Re-position guide curves and shuffle deck</b></p>
</div>


## Roadmap

- [x] code initial refactor
- [ ] more code refactor: isolate the rig to work without example file
- [ ] feature developments