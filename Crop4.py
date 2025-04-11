import tkinter as tk
from tkinter import filedialog
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk
import os

class CropImageApp:
    def __init__(self, root):
        self.zoom_factor = 1.0  # масштаб изображения
        self.MIN_ZOOM = 0.1
        self.MAX_ZOOM = 5.0

        self.root = root
        self.root.title("Image Cropper")
        self.root.geometry("900x700")

        self.dnd = root  # просто сохраняем ссылку, она уже drag-n-drop-совместимая
        self.canvas = tk.Canvas(self.dnd, cursor="cross", bg="gray")
        self.canvas.pack(fill="both", expand=True)
        self.square_crop = tk.BooleanVar(value=False)  # переключатель квадратного кропа

        # Переменные
        self.original_image = None
        self.display_image = None
        self.tk_image = None
        self.scale_ratio = 1
        self.image_path = None

        self.rect = None
        self.size_text = None
        self.start_x = self.start_y = None
        self.crop_box_display = None

        # Меню
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)
        self.menu.add_command(label="Open Image", command=self.open_image)
        options_menu = tk.Menu(self.menu, tearoff=0)
        options_menu.add_checkbutton(label="Фиксировать квадрат", onvalue=True, offvalue=False,
                                     variable=self.square_crop)
        self.menu.add_cascade(label="Опции", menu=options_menu)

        self.menu.add_command(label="Save", command=self.save_cropped_image)

        # События
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        #self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux scroll up
        #self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux scroll down

        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind("<<Drop>>", self.on_drop)

        self.canvas.bind("<Configure>", self.on_canvas_resize)

        self.window_resized = False

    def open_image(self):
        self.image_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.bmp;*.gif")]
        )
        if self.image_path:
            self.load_image(self.image_path)

    def load_image(self, file_path):
        self.original_image = Image.open(file_path)
        self.resize_and_display()

    def resize_and_display(self):
        if not self.original_image:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        img_width, img_height = self.original_image.size

        # Масштабируем с учётом окна и текущего зума
        fit_ratio = min(canvas_width / img_width, canvas_height / img_height)
        self.scale_ratio = fit_ratio * self.zoom_factor

        display_size = (
            int(img_width * self.scale_ratio),
            int(img_height * self.scale_ratio)
        )
        self.display_image = self.original_image.resize(display_size, Image.ANTIALIAS)

        self.tk_image = ImageTk.PhotoImage(self.display_image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        if self.size_text:
            self.canvas.delete(self.size_text)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, outline="red"
        )

    def on_mouse_drag(self, event):
        cur_x, cur_y = event.x, event.y
        dx = cur_x - self.start_x
        dy = cur_y - self.start_y

        if self.square_crop.get():
            # Делает квадратную область по меньшей из сторон
            side = min(abs(dx), abs(dy))
            cur_x = self.start_x + side * (1 if dx >= 0 else -1)
            cur_y = self.start_y + side * (1 if dy >= 0 else -1)

        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

        width = abs(cur_x - self.start_x)
        height = abs(cur_y - self.start_y)

        if self.size_text:
            self.canvas.delete(self.size_text)

        label = f"{int(width / self.scale_ratio)} x {int(height / self.scale_ratio)}"
        self.size_text = self.canvas.create_text(
            min(self.start_x, cur_x) + 5, min(self.start_y, cur_y) - 10,
            anchor="nw", text=label, fill="white", font=("Arial", 10, "bold")
        )

    def on_button_release(self, event):
        end_x, end_y = event.x, event.y

        dx = end_x - self.start_x
        dy = end_y - self.start_y

        if self.square_crop.get():
            # Делает квадратную область по меньшей из сторон
            side = min(abs(dx), abs(dy))
            end_x = self.start_x + side * (1 if dx >= 0 else -1)
            end_y = self.start_y + side * (1 if dy >= 0 else -1)

        x1, y1 = min(self.start_x, end_x), min(self.start_y, end_y)
        x2, y2 = max(self.start_x, end_x), max(self.start_y, end_y)
        self.crop_box_display = (x1, y1, x2, y2)

    def on_mouse_wheel(self, event):
        if not self.original_image:
            return

        # Колёсико вверх — увеличение, вниз — уменьшение
        if event.num == 5 or event.delta == -120:
            self.zoom_factor = max(self.MIN_ZOOM, self.zoom_factor - 0.1)
        elif event.num == 4 or event.delta == 120:
            self.zoom_factor = min(self.MAX_ZOOM, self.zoom_factor + 0.1)

        self.resize_and_display()

    def save_cropped_image(self):
        if not self.crop_box_display or not self.original_image:
            return

        x1, y1, x2, y2 = self.crop_box_display
        scale = 1 / self.scale_ratio
        crop_box_original = (int(x1 * scale), int(y1 * scale), int(x2 * scale), int(y2 * scale))

        cropped_image = self.original_image.crop(crop_box_original)

        # Убираем прозрачность, если формат не поддерживает
        if cropped_image.mode == "RGBA":
            cropped_image = cropped_image.convert("RGB")

        base, ext = os.path.splitext(self.image_path if self.image_path else "image.png")
        ext = ext if ext else ".png"  # если нет расширения — по умолчанию PNG

        new_image_path = f"{base}_crop{ext}"

        try:
            cropped_image.save(new_image_path)
            print(f"Изображение сохранено как {new_image_path}")
        except Exception as e:
            print(f"Ошибка при сохранении: {e}")

    def on_drop(self, event):
        file_path = event.data.strip().strip('{}').replace('\\', '/')
        if os.path.isfile(file_path):
            self.image_path = file_path
            self.load_image(file_path)

    def on_canvas_resize(self, event):
        # Перерисовка изображения при ресайзе окна
        if self.original_image:
            self.resize_and_display()

if __name__ == "__main__":
    from tkinterdnd2 import TkinterDnD

    root = TkinterDnD.Tk()
    app = CropImageApp(root)
    root.mainloop()
