from flask import Flask, render_template, request
from bentley_ottmann import bentley_ottmann, Point, Segment
import plotly.graph_objs as go
import plotly.offline as pyo

app = Flask(__name__)

# Uruchomienie aplikacji Flask, jeśli plik jest uruchamiany bezpośrednio
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    segments = []
    plot_html = None

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

            # --- Wizualizacja wyników z użyciem Plotly ---
            fig = go.Figure()

            # Rysowanie wszystkich odcinków
            for seg in segments:
                fig.add_trace(go.Scatter(
                    x=[seg.p.x, seg.q.x],
                    y=[seg.p.y, seg.q.y],
                    mode='lines+markers',
                    line=dict(color='gray'),
                    marker=dict(size=6, color='gray'),
                    showlegend=False
                ))

            # Rysowanie punktów przecięcia (z tooltipem)
            if points:
                fig.add_trace(go.Scatter(
                    x=[px for px, py in points],
                    y=[py for px, py in points],
                    mode='markers',
                    marker=dict(size=8, color='red'),
                    name='Punkty przecięcia',
                    text=[f'({px:.2f}, {py:.2f})' for px, py in points],
                    hoverinfo='text'
                ))

            # Rysowanie fragmentów wspólnych (pokrywających się odcinków)
            for (x1, y1), (x2, y2) in overlapping_segments:
                # Linia fragmentu wspólnego
                fig.add_trace(go.Scatter(
                    x=[x1, x2],
                    y=[y1, y2],
                    mode='lines',
                    line=dict(color='red', width=3),
                    showlegend=False
                ))
                # Markery na końcach z tooltipem
                fig.add_trace(go.Scatter(
                    x=[x1, x2],
                    y=[y1, y2],
                    mode='markers',
                    marker=dict(size=8, color='red'),
                    showlegend=False,
                    text=[f"({x1:.2f}, {y1:.2f})", f"({x2:.2f}, {y2:.2f})"],
                    hoverinfo='text'
                ))

            fig.update_layout(
                title="Wizualizacja przecięcia odcinków",
                xaxis_title="x",
                yaxis_title="y",
                width=1600,
                height=900
            )

            # Generuj kod HTML z wykresem Plotly
            plot_html = pyo.plot(fig, output_type='div', include_plotlyjs='cdn')

        except Exception as e:
            # Obsługa błędów formatu danych wejściowych
            result = f"Nieprawidłowy format odcinków."
            return render_template('index.html', result=result)

    # Wyświetl stronę z wynikami i (opcjonalnie) wykresem
    return render_template('index.html', result=result, plot_html=plot_html)
