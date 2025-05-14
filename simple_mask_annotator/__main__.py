#!/usr/bin/env python3
import os
import sys
import tkinter as tk

# Add the parent directory to sys.path to allow importing the package
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from simple_mask_annotator.ui.app import SimpleMaskAnnotatorApp

def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = SimpleMaskAnnotatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
