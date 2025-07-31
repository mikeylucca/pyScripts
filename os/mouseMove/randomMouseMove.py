from pynput import mouse, keyboard
import time
import random
import threading

running = True

def on_press(key):
	global running
	try:
		if key == keyboard.Key.esc:
			running = False
	except AttributeError:
		pass

def move_cursor():
	curr_x, curr_y = mouse.Controller().position
	
	offset_x = random.randint(-10, 10)
	offset_y = random.randint(-10, 10)
	
	new_x = max(0, offset_x + offset_x)
	new_y = max(0, offset_x + offset_y)
	
	mouse.Controller().position = (new_x, new_y)
	print(f"Moved cursor to X: {new_x}, Y: {new_y}")
	
	

def main():
	global running

	keyboard_listener = keyboard.Listener(on_press=on_press)
	keyboard_listener.start()

	print("Started")

	try:
		while running:
			move_cursor()
			time.sleep(5)
	except KeyboardInterrupt:
		running = False
		keyboard_listener.stop()
		print("Stopped by user\n")
	finally:
		keyboard_listener.stop()
		print("Stopped by user\n")

if __name__ == "__main__":
	main()