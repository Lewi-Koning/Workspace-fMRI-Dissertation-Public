# Some notes on Lab / scanner setup

Denis Schluppeck, 2026-06-03

## Scanner (3T Philips Ingenia)

![View through bore](images/IMG_0554.jpeg)View through bore

![General layout](images/IMG_0555.jpeg)General layout of scanner room (bed out)

![](images/IMG_0556.jpeg)View from console room

![](images/IMG_0557.jpeg)View through door - outside 5Gauss line

## Measurments + device info

- in the 3T, we have access to a BOLDscreen32 [technical details](https://www.crsltd.com/tools-for-functional-imaging/mr-safe-displays/boldscreen-32-lcd-for-fmri/) which is placed at the head end of the bore

- patient / participant is HFS (head-first-supine) and looks at screen through single or double mirror setup (small gotcha - with one mirror setup, code needs to flip images during rendering)

- measurements are the 3T display are

```json
{
  "screenNumber": 2,
  "screenWidth": 1920,
  "screenHeight": 1080,
  "framesPerSecond": 100,
  "displayDistance": 139,
  "displaySize": [
    69.66857,
    39.18857
  ],
  }
```

With a bit of trig that means the screen subtends ±14º of visual angle in width and ±8º of visual angle in height.

1º of visual angle $\approx$ 1cm at an arm's length.

| $\alpha = \tan^{-1}(w/2,d)$, where $w$ is `screenWidth` in cm and `d` is distance from eye to display in cm


