from hand_segmentation_tool_new import HandSegmentationTool
import tkinter as tk
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = HandSegmentationTool(root)
        root.mainloop()
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
