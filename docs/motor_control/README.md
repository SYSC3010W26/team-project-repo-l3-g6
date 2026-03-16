# MOTOR CONTROL SUBSYSTEM

## Hardware Components

  1. BigTreeTech SKR v1.4 Motor Control Board
  2. 5x BigTreeTech TMC2209 v1.3 Stepper Motor Driver
  3. 5x NEMA 17 2A Stepper Motor (4.2 x 4.2 x 4.8 cm)
  4. Raspberry Pi Model 4 with SenseHAT module.
  5. 24V 5A DC Power Supply. (Using variable lab bench supply)
  6. USB A to USB B data cable. (Comes with SKR v1.4)
  7. Spare MicroSD card for flashing Klipper firmware 

## Software Components

  1. Klipper firmware for SKR v1.4 control board. - Runs on control board
  2. Moonraker API for Klipper firmware - Runs on Pi
  3. Python 3+ script that sends and receives commands from server. - Runs on Pi
  4. OPTIONAL: Mainsail web dashboard for Klipper fimrware - Runs on Pi

## Subsystem Architecture Diagram

## Subsystem Wiring Diagram

## Manufacturer Documentation/Purchase Links 
  
  | Item | Manufacturer | Link to Product |
  | --- | --- | --- |
  | SKR v1.4 Motor Control Board | BigTreeTech | |
  | TMC2209 v1.3 Stepper Motor Driver | BigTreeTech | [BTT Wiki](https://github.com/bigtreetech/BIGTREETECH-Stepper-Motor-Driver/blob/master/TMC2209/V1.3/manual/BIGTREETECH%20TMC2209%20V1.3%20User%20Manual.pdf) |
  | NEMA 17 2A Stepper Motor | Many Manufacturers Available (We used StepperOnline) |[StepperOnline](https://www.stepperonline.ca/e-series-nema-17-bipolar-55ncm-77-88oz-in-2a-42x48mm-4-wires-w-1m-cable-connector-17he19-2004s.html) |
  | Raspberry Pi Model 4 | Raspberry Pi | [Rpi Docs](https://www.raspberrypi.com/documentation/) | 
  | SenseHAT Module | Raspberry Pi | [Rpi SenseHAT Docs](https://www.raspberrypi.com/documentation/accessories/sense-hat.html) | 
  | Variable DC Power Supply | Many Manufactuerers (Mine is Wanptek) | [Amazon CA](https://www.amazon.ca/Wanptek-Regulated-Variable-Presets-Protection/dp/B0FLJ9X32S/ref=sr_1_4?crid=13KVKRKUFVYHY&dib=eyJ2IjoiMSJ9._zb7o3QoizjmQzvtxCVVCURFiarP4EtfC5w1DwGDK1155EYJWbTw7gVX1gxC56QqU-Ao6moJYDBSTXl6g-GprS-cm-nJblyifMfLggAiTKA8KjOq9O4eQnBdv3zNX5_I.ZL1D26Ue8bgy9HK-pt2XFJIW_ypv-NV0-JVX5yYK7Es&dib_tag=se&keywords=wanptek+30v10a&qid=1773686666&sprefix=wanptek+30v10a%2Caps%2C109&sr=8-4) |
  | MicroSD Card | Many Manufacturers Available (Mine was Kingston 8GB) | [Amazon CA](https://www.amazon.ca/Micro-Ultra-Memory-Class-Cards/dp/B08C539851/ref=sr_1_6?crid=3BDFIH41PPHJ1&dib=eyJ2IjoiMSJ9.wCpqLrlRAqnJtrBPelquCzSbte_u2TBNq9vnvazkbR5MUS4Fih4nKH0x2aNCVJ2NqldVr5EXnq22hh0EjkOzE9_vR59oGhM5FRPx4E4SYSJwy6onlz6KfceYYMmxwZh3tRe2SabcvLS6z8NLClJq3rGfWiA3jJpZ2WZ_fWE-PjzHSCpMxIb-itBSYfgus6aPLF7wrTnvCjjKYspXNLyvGp8UN4pdGAlpfKDWc6kRAADzmt_VNoP8Sa7-HyWqdv6tpBGSADjBnx7o217LYEyuoPXiHRh7yD6We5NicQJnNCQ.yhh9v905PiR114V7a08Qk_aFzVYRVJWcSykl5cFxlzM&dib_tag=se&keywords=microsd&qid=1773686738&sprefix=microsd%2Caps%2C121&sr=8-6) |
  
