import tkinter as tk
from tkinter import filedialog
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk
import os
import re

class CropImageApp:
    def __init__(self, root):
        self.zoom_factor = 1.0  # масштаб изображения
        self.MIN_ZOOM = 0.1
        self.MAX_ZOOM = 5.0

        self.root = root
        self.root.title("ОБРЕЗОК by RomixERR")
        self.root.geometry("900x700")

        self.dnd = root  # просто сохраняем ссылку, она уже drag-n-drop-совместимая
        self.canvas = tk.Canvas(self.dnd, cursor="cross", bg="gray")
        self.canvas.pack(fill="both", expand=True)
        self.square_crop = tk.BooleanVar(value=False)  # переключатель квадратного кропа
        self.version_index_save = tk.BooleanVar(value=True)  # переключатель сохранения версий или всегда заменять

        # Переменные
        self.original_image = None
        self.display_image = None
        self.tk_image = None
        self.scale_ratio = 1
        self.image_path = None

        self.rect = None
        self.size_text = None
        self.start_x = self.start_y = None
        self.cur_x = self.cur_y = None
        self.smesh_x = self.smesh_y = None
        self.crop_box_display = None
        self.zoom_shift_x = self.zoom_shift_y = .0

        # Меню
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)
        self.menu.add_command(label="Open Image", command=self.open_image)
        options_menu = tk.Menu(self.menu, tearoff=0)
        options_menu.add_checkbutton(label="Фиксировать квадрат", onvalue=True, offvalue=False,
                                     variable=self.square_crop)
        options_menu.add_checkbutton(label="Сохранять новые версии в разные файлы", onvalue=True, offvalue=False,
                                     variable=self.version_index_save)
        options_menu.add_command(label="Zoom reset",command=self.reset_zoom)
        options_menu.add_command(label="Rotate image 90 deg right", command=self.rotate_image)

        self.menu.add_cascade(label="Опции", menu=options_menu)

        self.menu.add_command(label="Save", command=self.save_cropped_image)

        # События
        self.canvas.bind("<ButtonPress-1>", self.on_button_press_1)
        self.canvas.bind("<ButtonPress-3>", self.on_button_press_3)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag_1)
        self.canvas.bind("<B3-Motion>", self.on_mouse_drag_3)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release_1)
        self.canvas.bind("<ButtonRelease-3>", self.on_button_release_3)
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

    def load_image(self, file_path ):
        self.original_image = Image.open(file_path)
        self.resize_and_display(None)

    def reset_zoom(self):
        self.zoom_shift_x = 0
        self.zoom_shift_y = 0
        self.zoom_factor = 1
        self.resize_and_display(None)

    def resize_and_display(self, event):
        if not self.original_image:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_width, img_height = self.original_image.size

        fit_ratio = min(canvas_width / img_width, canvas_height / img_height)

        # Сохраняем старый масштаб и сдвиг
        old_scale = self.scale_ratio
        old_shift_x = self.zoom_shift_x
        old_shift_y = self.zoom_shift_y

        self.scale_ratio = fit_ratio * self.zoom_factor

        if event:
            # Координаты курсора в пространстве изображения ДО зума
            image_x = (event.x - old_shift_x) / old_scale
            image_y = (event.y - old_shift_y) / old_scale

            # Новые сдвиги так, чтобы курсор указывал на ту же точку
            self.zoom_shift_x = event.x - image_x * self.scale_ratio
            self.zoom_shift_y = event.y - image_y * self.scale_ratio
        else:
            # Центрируем по умолчанию
            self.zoom_shift_x = (canvas_width - img_width * self.scale_ratio) / 2
            self.zoom_shift_y = (canvas_height - img_height * self.scale_ratio) / 2

        display_size = (
            int(img_width * self.scale_ratio),
            int(img_height * self.scale_ratio)
        )

        self.display_image = self.original_image.resize(display_size, Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(self.display_image)
        self.canvas.delete("all")
        self.canvas.create_image(self.zoom_shift_x, self.zoom_shift_y, anchor="nw", image=self.tk_image)

    def on_button_press_1(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        if self.size_text:
            self.canvas.delete(self.size_text)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, outline="red"
        )
    def on_button_press_3(self, event):
        print()
        self.smesh_x = event.x-self.start_x
        self.smesh_y = event.y - self.start_y



    def on_mouse_drag_1(self, event):
        self.cur_x, self.cur_y = event.x, event.y
        dx = self.cur_x - self.start_x
        dy = self.cur_y - self.start_y

        if self.square_crop.get():
            # Делает квадратную область по меньшей из сторон
            side = min(abs(dx), abs(dy))
            self.cur_x = self.start_x + side * (1 if dx >= 0 else -1)
            self.cur_y = self.start_y + side * (1 if dy >= 0 else -1)

        self.canvas.coords(self.rect, self.start_x, self.start_y, self.cur_x, self.cur_y)

        width = abs(self.cur_x - self.start_x)
        height = abs(self.cur_y - self.start_y)

        if self.size_text:
            self.canvas.delete(self.size_text)

        label = f"{int(width / self.scale_ratio)} x {int(height / self.scale_ratio)}"
        self.size_text = self.canvas.create_text(
            min(self.start_x, self.cur_x) + 5, min(self.start_y, self.cur_y) - 10,
            anchor="nw", text=label, fill="white", font=("Arial", 10, "bold")
        )

    def on_mouse_drag_3(self, event):
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        self.cur_x = self.cur_x + dx-self.smesh_x
        self.cur_y = self.cur_y + dy-self.smesh_y
        self.start_x = self.start_x + dx-self.smesh_x
        self.start_y = self.start_y + dy-self.smesh_y

        self.canvas.coords(self.rect, self.start_x, self.start_y, self.cur_x, self.cur_y)

        width = abs(self.cur_x - self.start_x)
        height = abs(self.cur_y - self.start_y)

        if self.size_text:
            self.canvas.delete(self.size_text)

        label = f"{int(width / self.scale_ratio)} x {int(height / self.scale_ratio)}"
        self.size_text = self.canvas.create_text(
            min(self.start_x, self.cur_x) + 5, min(self.start_y, self.cur_y) - 10,
            anchor="nw", text=label, fill="white", font=("Arial", 10, "bold")
        )

    def on_button_release_1(self, event):
        x1,y1,x2,y2=self.start_x,self.start_y,self.cur_x,self.cur_y
        self.crop_box_display = (x1, y1, x2, y2)


    def on_button_release_3(self, event):
        x1,y1,x2,y2=self.start_x,self.start_y,self.cur_x,self.cur_y
        self.crop_box_display = (x1, y1, x2, y2)


    def on_mouse_wheel(self, event):
        if not self.original_image:
            return

        # Колёсико вверх — увеличение, вниз — уменьшение
        if event.num == 5 or event.delta == -120:
            self.zoom_factor = max(self.MIN_ZOOM, self.zoom_factor - self.zoom_factor/5)
        elif event.num == 4 or event.delta == 120:
            self.zoom_factor = min(self.MAX_ZOOM, self.zoom_factor + self.zoom_factor/5)

        self.resize_and_display(event)

    def save_cropped_image(self):
        if not self.crop_box_display or not self.original_image:
            return

        xt1, yt1, xt2, yt2 = self.crop_box_display
        x1 = min(xt1, xt2)
        y1 = min(yt1, yt2)
        x2 = max(xt1, xt2)
        y2 = max(yt1, yt2)

        scale = 1 / self.scale_ratio
        crop_box_original = (int((x1 - self.zoom_shift_x) * scale), int((y1 - self.zoom_shift_y) * scale), int((x2 - self.zoom_shift_x) * scale), int((y2 - self.zoom_shift_y) * scale))

        cropped_image = self.original_image.crop(crop_box_original)

        # Убираем прозрачность, если формат не поддерживает
        if cropped_image.mode == "RGBA":
            cropped_image = cropped_image.convert("RGB")

        base, ext = os.path.splitext(self.image_path if self.image_path else "image.png")
        ext = ext if ext else ".png"  # если нет расширения — по умолчанию PNG

        new_image_path = f"{base}_crop{ext}" #сохранение будет происходить всегда в один и то-же файл (_crop)
        if self.version_index_save.get():
            new_image_path = self.versioned_path(new_image_path) #сохранение всех версий со счётчиком

        try:
            cropped_image.save(new_image_path)
            print(f"Изображение сохранено как {new_image_path}")
        except Exception as e:
            print(f"Ошибка при сохранении: {e}")

    def versioned_path(self,image_path):  #именование файлов со счётчиком
        folder = os.path.dirname(image_path)
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        extension = os.path.splitext(image_path)[1]  # Например, ".jpg"

        # Регулярка для поиска файлов типа image_01.jpg
        pattern = re.compile(rf"^{re.escape(base_name)}_(\d+){re.escape(extension)}$")

        max_index = 0
        for file in os.listdir(folder):
            match = pattern.match(file)
            if match:
                index = int(match.group(1))
                if index > max_index:
                    max_index = index
        new_index = max_index + 1
        new_filename = f"{base_name}_{new_index:02d}{extension}"
        new_path = os.path.join(folder, new_filename)
        return new_path
    def rotate_image(self):
        self.original_image = self.original_image.rotate(angle=90,expand=True)
        self.resize_and_display(None)

    def on_drop(self, event):
        file_path = event.data.strip().strip('{}').replace('\\', '/')
        if os.path.isfile(file_path):
            self.image_path = file_path
            self.load_image(file_path)

    def on_canvas_resize(self, event):
        # Перерисовка изображения при ресайзе окна
        if self.original_image:
            self.resize_and_display(None)

if __name__ == "__main__":
    from tkinterdnd2 import TkinterDnD

    root = TkinterDnD.Tk()
    app = CropImageApp(root)
    root.mainloop()
