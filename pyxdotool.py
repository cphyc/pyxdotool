import subprocess

xdt = 'xdotool'

def call(fun):
    def wrapper(*args):
        proc = subprocess.run([xdg] + fun(*args))
        if proc.returncode == 0:
            return proc
        else:
            return None
        
class Instruction:
    counter = 0
    
    def __init__(self, instructions=None):
        self.instructions = instructions if instructions is not None else []
        self.callbacks = {}
        self.stdout = None
        self.stderr = None
        self.returncode = None

    def exec(self):
        proc = subprocess.run([xdt] + self.instructions,
                              stdout=subprocess.PIPE,
                              universal_newlines=True)
        if proc.returncode == 0:
            stdout = proc.stdout.split('\n')
            stdoutgen = (l for l in stdout) # generator form
            cbs = self.callbacks
            self.raw_stdout = proc.stdout
            self.stdout = [cbs[i](stdoutgen) for i in range(self.counter)]
        else:
            self.stdout = proc.stdout
            self.sterr = proc.stderr
            
        self.returncode = proc.returncode
        return self

    def _consumeArgs(self, out):
        if type(out) == tuple:
            _mine, _pass = out[0], out[1:]
            _pass = self if len(_pass) == 0 else _pass
        else:
            _mine = out
            _pass = self
        return _mine, _pass
            
    def addInstr(fun):
        def wrapper(_self, *args, **kwargs):
            out = fun(_self, *args, **kwargs)
            _mine, _pass = _self._consumeArgs(out)
            
            _self.instructions.extend([str(ins) for ins in _mine])
            return _pass
        
        return wrapper

    def addCallback(fun):
        def wrapper(_self, *args, **kwargs):
            out = fun(_self, *args, **kwargs)
            _mine, _pass = _self._consumeArgs(out)
            
            _self.callbacks[_self.counter] = _mine
            _self.counter += 1
            return _pass
        return wrapper

    def _intParser(self, gen):
        line = next(gen)
        return int(line)
    
    def _geomParser(self, gen):
        ''' Extract the geometry from a line: Geomtry: WxH'''
        line = next(gen)
        W, H = [int(e) for e in line.split(':')[1].split('x')]
        return {'width': W, 'heigth': H}

    def _positionParser(self, gen):
        line = next(gen)
        tmp = [int(e) for e in line.split(': ')[1].split(' (')[0].split(',')]
        X, Y = tmp
        return {'x': X, 'y': Y}

    def _emptyParser(self, gen):
        next(gen)
        return {}
    
    def compose(self, *args):
        obj = {}
        def wrapped(gen):
            for parser in args:
                tmp = parser(gen)
                obj.update(tmp)

            return obj
        return wrapped


    @addInstr
    @addCallback
    def getActiveWindow(self):
        return (lambda g: {'window': self._intParser(g)}, ['getactivewindow'])

    @addInstr
    @addCallback
    def getWindowFocus(self):
        return (lambda g: {'window': self._intParser(g)}, ['getwindowfocus'])

    @addInstr
    @addCallback
    def getWindowName(self, *args):
        return (lambda g: {'window_name': next(g)},
                ['getwindowname'] + list(args))

    @addInstr
    @addCallback
    def getWindowPid(self, *args):
        return (lambda g: {'window_pid': self._intParser(g)},
                ['getwindowpid'] + list(args))

    @addInstr
    @addCallback
    def getWindowGeometry(self, *args):
        parser = self.compose(self._emptyParser, self._positionParser, self._geomParser)
        return (lambda g: {'window_geometry': parser(g)},
                ['getwindowgeometry'] + list(args))

    
    @addInstr
    @addCallback
    def getDisplayGeometry(self):
        def parser(g):
            l = [int(e) for e in next(g).split()]
            return {'x': l[0], 'y': l[1]}
            
        return (lambda g: {'window_geometry': parser(g)},
                ['getdisplaygeometry'])

    def parseOptions(self, **kwargs):
        opts = []
        for key in kwargs:
            if kwargs[key] is True:
                opts.extend(['--' + key])
            elif kwargs[key] is not False:
                opts.extend('--' + key, kwargs[key])

        return opts

    @addInstr
    @addCallback
    def search(self, regexp, *args, **kwargs):
        print('For now, only the first results will be saved')
        parser = lambda g: self._intParser(g)
        instructions = ['search'] + self.parseOptions(**kwargs) + [regexp]

        return (parser, instructions)

    
    @addInstr
    @addCallback
    def selectWindow(self):
        parser = lambda g: self._intParser(g)
        return (parser, ['selectwindow'])
            
    def behave(self):
        print('Unsupported')
        
    def behaveScreenEdge(self):
        print('Unsupported')

    @addInstr
    def click(self, button, **kwargs):
        return (['click'] + self.parseOptions(**kwargs) + [button])

    @addInstr
    @addCallback
    def getMouseLocation(self):
        def parser(g):
            line = next(g)
            x, y, screen, window = [int(e.split(':')[1]) for e in line.split()]
            return { 'x': x, 'y': y, 'screen': screen, 'window': window }
                                    
        return (lambda g: parser(g), ['getmouselocation'])

    @addInstr
    def key(self, key, *keys, **kwargs):
        return (['key'] + self.parseOptions(**kwargs) + [key] + list(keys))

    @addInstr
    def keyDown(self, key, *keys, **kwargs):
        return (['keydown'] + self.parseOptions(**kwargs) + [key] + list(keys))

    @addInstr
    def keyUp(self, key, *keys, **kwargs):
        return (['keydown'] + self.parseOptions(**kwargs) + [key] + list(keys))

    @addInstr
    def mouseDown(self, key, *keys, **kwargs):
        return (['mousedown'] + self.parseOptions(**kwargs) + [key] + list(keys))

    @addInstr
    def mouseUp(self, key, *keys, **kwargs):
        return (['mouseup'] + self.parseOptions(**kwargs) + [key] + list(keys))
    @addInstr
    def mouseMove(self, x, y, relative=False, **kwargs):
        if relative == True:
            return self._mouseMoveRelative(x, y, **kwargs)
        else:
            return (['mousemove'] + self.parseOptions(**kwargs) + ['--', str(x), str(y)])

    @addInstr
    def mouseMoveRelative(self, *args, **kwargs):
        return self._mouseMoveRelative(self, *args, **kwargs)
    
    def _mouseMoveRelative(self, dx, dy, **kwargs):
        return (['mousemove_relative'] + self.parseOptions(**kwargs) + ['--', str(dx), str(dy)])

    @addInstr
    def setWindow(self, window=None, **kwargs):
        l_window = [window] if window is not None else []
        return (['set_window'] + self.parseOptions(**kwargs) + l_window)
    
    @addInstr
    def type(self, args):
        return (['type', args])

    @addInstr
    def windowActivate(self, window=None, **kwargs):
        l_window = [window] if window is not None else []
        return (['windowactivate'] + self.parseOptions(**kwargs) + l_window)

    @addInstr
    def windowFocus(self, window=None, **kwargs):
        l_window = [window] if window is not None else []
        return (['windowfocus'] + self.parseOptions(**kwargs) + l_window)

    @addInstr
    def windowKill(self, window=None):
        l_window = [window] if window is not None else []
        return (['windowkill'] + l_window)

    @addInstr
    def windowMap(self, window=None, **kwargs):
        l_window = [window] if window is not None else []
        return (['windowmap'] + self.parseOptions(**kwargs) + l_window)

    @addInstr
    def windowMinimize(self, window=None, **kwargs):
        l_window = [window] if window is not None else []
        return (['windowminimize'] + self.parseOptions(**kwargs) + l_window) 
    
    @addInstr
    def windowMove(self, x, y, window=None, **kwargs):
        l_window = [window] if window is not None else []
        return (['windowminimize'] + self.parseOptions(**kwargs) +
                l_window + [str(x), str(y)])

    @addInstr
    def windowRaise(self, window=None, **kwargs):
        l_window = [window] if window is not None else []
        return (['windowraise'] + self.parseOptions(**kwargs) + l_window) 

    @addInstr
    def windowReparent(self, windowDestination, windowSource=None, **kwargs):
        l_window = [window] if window is not None else []
        return (['windowreparent'] + self.parseOptions(**kwargs) +
                l_window + [str(windowDestination)])
    
    @addInstr
    def windowSize(self, width, height, window=None, **kwargs):
        l_window = [window] if window is not None else []
        return (['windowminimize'] + self.parseOptions(**kwargs) +
                l_window + [str(width), str(height)])

    @addInstr
    def windowUnmap(self, window=None, **kwargs):
        l_window = [window] if window is not None else []
        return (['windowunmap'] + self.parseOptions(**kwargs) + l_window)

    @addInstr
    def setNumDesktop(self, n):
        return (['set_num_desktops', str(n)])

    @addInstr
    @addCallback
    def getNumDesktops(self):
        parser = lambda g: {'n_desktop': self._intParser(g)}
        return (parser, ['get_num_desktops'])
    
    @addInstr
    def setDesktop(self, n, **kwargs):
        return (['set_desktop'] + self.parseOptions(**kwargs) + [str(n)])

    @addInstr
    @addCallback
    def getDesktop(self):
        parser = lambda g: {'desktop': self._intParser(g)}
        return (parser, ['get_desktop'])

    @addInstr
    def setDesktopForWindow(self, n, window=None, **kwargs):
        l_window = [window] if window is not None else []
        return (['set_desktop_for_window'] + self.parseOptions(**kwargs) + l_window + [str(n)])

    @addInstr
    @addCallback
    def getDesktopForWindow(self):
        l_window = [window] if window is not None else []
        parser = lambda g: {'desktop': self._intParser(g)}
        return (parser, ['get_desktop_for_window'] + l_window)

    def setDesktopViewport(self):
        print('Unsupported')

    def getDesktopViewport(self):
        print('Unsupported')
        
    @addInstr
    def sleep(self, time):
        return (['sleep', time])
