from heapq import heappush, heappop
from uuid import uuid4

# Definicje struktur danych
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __eq__(self, other):
        return isinstance(other, Point) and abs(self.x - other.x) < 1e-8 and abs(self.y - other.y) < 1e-8
    def __hash__(self):
        return hash((round(self.x, 8), round(self.y, 8)))
    def __repr__(self):
        return f"Point({self.x}, {self.y})"

class Segment:
    def __init__(self, p, q, seg_id=None):
        self.p = p
        self.q = q
        self.id = seg_id if seg_id is not None else uuid4()
    def __eq__(self, other):
        return isinstance(other, Segment) and self.id == other.id
    def __hash__(self):
        return hash(self.id)
    def __repr__(self):
        return f"Segment({self.p}, {self.q}, id={self.id})"

class Event:
    """
    Klasa reprezentująca zdarzenie w kolejce zdarzeń.
    kind: 'start', 'end', 'intersect'
    segments: lista segmentów związanych ze zdarzeniem
    """
    def __init__(self, point, kind, segments):
        self.point = point
        self.kind = kind
        self.segments = segments

    def __lt__(self, other):
        return (self.point.x, self.point.y) < (other.point.x, other.point.y)

def normalize_segment(p, q, seg_id=None):
    """
    Zwraca segment o uporządkowanych końcach (najpierw mniejszy punkt).
    """
    if (p.x, p.y) < (q.x, q.y):
        return Segment(p, q, seg_id)
    else:
        return Segment(q, p, seg_id)

def det(a, b):
    """
    Wyznacznik dwóch wektorów (pomocnicze do obliczeń geometrycznych).
    """
    return a.x * b.y - a.y * b.x

def segment_y_at(segment, x):
    """
    Zwraca współrzędną y punktu przecięcia segmentu z pionową prostą x=const.
    """
    if segment.p.x == segment.q.x:
        return min(segment.p.y, segment.q.y)
    t = (x - segment.p.x) / (segment.q.x - segment.p.x)
    return segment.p.y + t * (segment.q.y - segment.p.y)

def segment_intersection(s1, s2):
    """
    Zwraca punkt przecięcia dwóch odcinków (lub odcinek, jeśli współliniowe i nakładają się),
    lub None jeśli się nie przecinają.
    """
    if s1.id == s2.id:
        return None
    p, r = s1.p, Point(s1.q.x - s1.p.x, s1.q.y - s1.p.y)
    q, s = s2.p, Point(s2.q.x - s2.p.x, s2.q.y - s2.p.y)
    denom = det(r, s)
    qp = Point(q.x - p.x, q.y - p.y)

    if denom == 0:
        if det(qp, r) != 0:
            return None
        def project_onto(v, base):
            return (v.x * base.x + v.y * base.y) / (base.x**2 + base.y**2)
        t0 = 0
        t1 = 1
        u0 = project_onto(Point(s2.p.x - s1.p.x, s2.p.y - s1.p.y), r)
        u1 = project_onto(Point(s2.q.x - s1.p.x, s2.q.y - s1.p.y), r)
        t_start = max(min(t0, t1), min(u0, u1))
        t_end = min(max(t0, t1), max(u0, u1))
        if t_start > t_end:
            return None
        elif t_start == t_end:
            x = p.x + t_start * r.x
            y = p.y + t_start * r.y
            return Point(x, y)
        else:
            p1 = Point(p.x + t_start * r.x, p.y + t_start * r.y)
            p2 = Point(p.x + t_end * r.x, p.y + t_end * r.y)
            return normalize_segment(p1, p2)
    t = det(qp, s) / denom
    u = det(qp, r) / denom

    if 0 <= t <= 1 and 0 <= u <= 1:
        return Point(p.x + t * r.x, p.y + t * r.y)

    return None

def bentley_ottmann(segments):
    """
    Główna funkcja algorytmu Bentley-Ottmann.
    Przyjmuje listę odcinków, zwraca listę punktów przecięcia i odcinków wspólnych.
    """
    # Uporządkuj końce odcinków
    segments = [normalize_segment(s.p, s.q, s.id) for s in segments]
    event_queue = []  # kolejka zdarzeń
    status = []       # status (lista aktywnych odcinków)
    point_result = set()    # zbiór punktów przecięcia
    segment_result = set()  # zbiór odcinków wspólnych
    added_intersections = set()  # zapamiętane przecięcia (by nie dublować)

    # Dodaj do kolejki zdarzeń punkty początkowe i końcowe wszystkich odcinków
    for seg in segments:
        heappush(event_queue, Event(seg.p, 'start', [seg]))
        heappush(event_queue, Event(seg.q, 'end', [seg]))

    # Główna pętla przetwarzania zdarzeń
    while event_queue:
        event = heappop(event_queue)
        x, y = event.point.x, event.point.y
        # Pobierz wszystkie zdarzenia w tym samym punkcie
        events_same_point = [event]
        while event_queue and event_queue[0].point.x == x and event_queue[0].point.y == y:
            events_same_point.append(heappop(event_queue))

        # Podziel zdarzenia na typy
        start_segs, end_segs, intersect_segs = [], [], []
        for e in events_same_point:
            if e.kind == 'start':
                start_segs.extend(e.segments)
            elif e.kind == 'end':
                end_segs.extend(e.segments)
            elif e.kind == 'intersect':
                intersect_segs.extend(e.segments)
                # Dodaj punkt przecięcia do wyniku
                key = (round(e.point.x, 8), round(e.point.y, 8))
                point_result.add((e.point.x, e.point.y))

        # --- KLUCZOWA POPRAWKA: dodaj punkt przecięcia, jeśli w tym punkcie spotyka się więcej niż jeden segment
        involved_segs = set(start_segs + end_segs + intersect_segs)
        if len(involved_segs) > 1:
            key = (round(x, 8), round(y, 8))
            point_result.add((x, y))

        # Usuń kończące się segmenty ze statusu
        for seg in end_segs:
            if seg in status:
                status.remove(seg)

        # Zamień miejscami segmenty, które się przecinają (potrzebne do poprawnego statusu)
        for i in range(len(intersect_segs)):
            for j in range(i + 1, len(intersect_segs)):
                if intersect_segs[i] in status and intersect_segs[j] in status:
                    idx1 = status.index(intersect_segs[i])
                    idx2 = status.index(intersect_segs[j])
                    if abs(idx1 - idx2) == 1:
                        status[idx1], status[idx2] = status[idx2], status[idx1]

        # Dodaj zaczynające się segmenty do statusu (w odpowiedniej kolejności)
        for seg in start_segs:
            y_at_x = segment_y_at(seg, x)
            idx = 0
            while idx < len(status) and segment_y_at(status[idx], x) < y_at_x:
                idx += 1
            status.insert(idx, seg)

        # Sprawdź przecięcia dla wszystkich par segmentów w statusie (po dodaniu nowych)
        for seg in start_segs:
            for other in status:
                if seg == other:
                    continue
                inter = segment_intersection(seg, other)
                if isinstance(inter, Point):
                    key = (round(inter.x, 8), round(inter.y, 8))
                    if key not in added_intersections:
                        added_intersections.add(key)
                        heappush(event_queue, Event(inter, 'intersect', [seg, other]))
                elif isinstance(inter, Segment):
                    key = (
                        round(inter.p.x, 8), round(inter.p.y, 8),
                        round(inter.q.x, 8), round(inter.q.y, 8)
                    )
                    if key not in added_intersections:
                        added_intersections.add(key)
                        segment_result.add(((inter.p.x, inter.p.y), (inter.q.x, inter.q.y)))

    # Zwróć posortowane wyniki
    return sorted(point_result), sorted(segment_result)