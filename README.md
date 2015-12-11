# pyxdotool
Python bindings for xdotool.

It supports all the functions of xdotool and is fully chainable.

## Examples:
import xdotool

    # you can chain your instructions
    ins = pyxdotool.Instruction().mouseMoveRelative(100, 100).sleep(2).click()
	# it is not executed until you do
    ins.exec()

    # the results of stdout / stderr are found in
	ins = pyxdotool.Instruction().activeWindow().exec()
	activeWindow = ins.stdout[0]['window']

    wname = pyxdotool.Instruction().getWindowName(activeWindow).exec()
    print(wname)
