import sys
import os

# Set up path to include 'src' directory
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.append(src_dir)

if __name__ == "__main__":
    try:
        from main import MainApp
        app = MainApp()
        app.mainloop()
    except ImportError as e:
        print(f"Error starting application: {e}")
        print(f"Python path: {sys.path}")
        input("Press Enter to exit...")
