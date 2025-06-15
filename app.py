from flask import Flask, render_template, request
import matplotlib.pyplot as plt
import uuid
from bentley_ottmann import bentley_ottmann, Point, Segment

app = Flask(__name__)

# Uruchomienie aplikacji Flask, jeśli plik jest uruchamiany bezpośrednio
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    segments = []
    image_path = None

    if request.method == 'POST':
        # Obsługa wczytywania pliku CSV z odcinkami
        if 'csvFile' in request.files and request.files['csvFile'].filename != '':
            try:
                file = request.files['csvFile']
                content = file.read().decode('utf-8')
                raw_segments = content.strip().split(';')
            except Exception:
                result = "Błąd podczas odczytu pliku CSV. Upewnij się, że plik jest poprawny."
                return render_template('index.html', result=result)
        else:
            # Pobierz odcinki wpisane ręcznie w formularzu
            raw_segments = request.form.getlist('segments[]')

        # Sprawdzenie czy podano co najmniej dwa odcinki
        if not raw_segments or len(raw_segments) < 2:
            result = "Proszę podać co najmniej dwa odcinki."
            return render_template('index.html', result=result)

        try:
            # Parsowanie odcinków z danych wejściowych
            for seg in raw_segments:
                x1, y1, x2, y2 = map(float, seg.replace(',', ' ').split())
                segments.append(Segment(Point(x1, y1), Point(x2, y2)))

            # Wywołanie algorytmu Bentley-Ottmann
            points, overlapping_segments = bentley_ottmann(segments)

            # Przygotowanie tekstowego wyniku
            if not points and not overlapping_segments:
                result = "Brak przecięć między odcinkami."
            else:
                res = []
                if points:
                    res.append("Punkty przecięcia:")
                    for px, py in points:
                        res.append(f"({px:.2f}, {py:.2f})")
                if overlapping_segments:
                    res.append("\nWspólne odcinki (pokrywające się):")
                    for (x1, y1), (x2, y2) in overlapping_segments:
                        res.append(f"od ({x1:.2f}, {y1:.2f}) do ({x2:.2f}, {y2:.2f})")
                result = "\n".join(res)

        except Exception as e:
            # Obsługa błędów formatu danych wejściowych
            result = f"Nieprawidłowy format odcinków. Upewnij się, że każdy odcinek jest w formacie: x1,y1 x2,y2"
            return render_template('index.html', result=result)

        # --- Wizualizacja wyników ---
        fig, ax = plt.subplots()
        # Rysowanie wszystkich odcinków
        for seg in segments:
            ax.plot([seg.p.x, seg.q.x], [seg.p.y, seg.q.y], color='gray')
            ax.plot(seg.p.x, seg.p.y, 'o', color='gray')
            ax.plot(seg.q.x, seg.q.y, 'o', color='gray')
            ax.text(seg.p.x + 0.2, seg.p.y + 0.2, f"({seg.p.x:.2f}, {seg.p.y:.2f})", fontsize=5, color='gray')
            ax.text(seg.q.x + 0.2, seg.q.y + 0.2, f"({seg.q.x:.2f}, {seg.q.y:.2f})", fontsize=5, color='gray')

        # Rysowanie punktów przecięcia
        for px, py in points:
            ax.plot(px, py, 'ro')
            ax.text(px + 0.2, py + 0.2, f"({px:.2f}, {py:.2f})", fontsize=5, fontweight='bold', color='red')

        # Rysowanie fragmentów wspólnych (pokrywających się odcinków)
        for (x1, y1), (x2, y2) in overlapping_segments:
            ax.plot([x1, x2], [y1, y2], color='red', linewidth=2)
            ax.plot(x1, y1, 'ro')
            ax.plot(x2, y2, 'ro')
            ax.text(x1 - 0.3, y1 + 0.3, f"({x1:.2f}, {y1:.2f})", fontsize=5, fontweight='bold', color='red')
            ax.text(x2 + 0.3, y2 - 0.3, f"({x2:.2f}, {y2:.2f})", fontsize=5, fontweight='bold', color='red')

        # Ustawienia wykresu
        ax.set_title("Wizualizacja przecięcia odcinków")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.grid(True)
        ax.set_aspect('equal', 'box')

        # Automatyczne dopasowanie zakresu osi z marginesem
        all_x = [p.x for seg in segments for p in [seg.p, seg.q]]
        all_y = [p.y for seg in segments for p in [seg.p, seg.q]]

        padding = 1
        x_min, x_max = min(all_x), max(all_x)
        y_min, y_max = min(all_y), max(all_y)

        x_range = max(4, x_max - x_min)
        y_range = max(4, y_max - y_min)

        ax.set_xlim(x_min - padding, x_min + x_range + padding)
        ax.set_ylim(y_min - padding, y_min + y_range + padding)

        # Zapisz wykres do pliku w katalogu static/
        image_path = f"static/plot_{uuid.uuid4().hex}.png"
        fig.savefig(image_path, dpi=200)
        plt.close(fig)

    # Wyświetl stronę z wynikami i (opcjonalnie) wykresem
    return render_template('index.html', result=result, image_path=image_path)