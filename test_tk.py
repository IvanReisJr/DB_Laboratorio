import tkinter
try:
    root = tkinter.Tk()
    print("Tkinter works")
    root.destroy()
except Exception as e:
    print(f"Tkinter failed: {e}")
