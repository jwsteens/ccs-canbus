# CCS CAN bus

## Softwarebeschrijving
Pico 1 bevat PID-regelaar en stuurt MOSFET aan met PWM signaal.
Pico 2 leest temperatuursensor uit en stuurt deze waarde op de CAN bus.
Pico 3 leest waarde van potmeter uit en stuurt deze waarde op de CAN bus. Temperatuur en PWM waarde worden weergegeven op een OLED display.
Verder is het systeem uitgerust met foutdetectie. Wanneer de temperatuursensor geen waarde doorstuurt of de algehele verbinding met deze node wegvalt, wordt het setpoint op nul gezet. Wanneer pico 1 geen setpoint ontvangt, wordt de PWM waarde op 0 gezet. Wanneer de temperatuursensor niet in het aluminiumblokje zit, of wanneer de spanningsbron voor de weerstand niet aan staat, zal het systeem dit na ca. 2 minuten doorhebben en zal pico 1 uitschakelen.

## Gebruiksaanwijzing
Setup:
1. Aansluiten van componenten en bekabeling volgens schema:
	- Heater
	- MOSFET
	- Temperatuursensor
	- Potmeter
	- OLED scherm
	- Pico's
	- CAN modules
	- evt. UART
2. Installeren van de software:
	Pico 1:
	- `main.py` (pico 1)
	- `pid.py`
	- `pwm.py`
	- `MCP2515.py`
	- `canio.py`
	Pico 2:
	- `main.py` (pico 2)
	- `temperature_probe.py`
	- `MCP2515.py`
	- `canio.py`
	Pico 3:
	- `main.py` (pico 3)
	- `pico_functions_v1_1.py`
	- `MCP2515.py`
	- `canio.py`
3. Spanningsbron aansluiten

Gebruik:
1. Controleer groene LEDs op alle drie de Pico's
2. Gebruik potmeter om setpoint aan te passen
3. Regelconstanten kunnen worden aangepast in `main.py` van pico 1.
