import cv2
import dlib

cap = cv2.VideoCapture(0)
detector = dlib.get_frontal_face_detector()
if not cap.isOpened():
    raise SystemExit("Webcam non trovata")

SCALA = 0.5  # detection su immagine dimezzata 

while True:
    ret, img = cap.read()
    if not ret:
        break
    img = cv2.flip(img, 1) 

    # immagine piccola solo per la detection
    ip = cv2.resize(img, None, fx=SCALA, fy=SCALA)
    rgb = cv2.cvtColor(ip, cv2.COLOR_BGR2RGB)

    detected = detector(rgb, 0)

    for d in detected:
        x1 = int(d.left() / SCALA)
        y1 = int(d.top() / SCALA)
        x2 = int((d.right() + 1) / SCALA)
        y2 = int((d.bottom() + 1) / SCALA)
        cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)

    cv2.imshow("result", img)
    if cv2.waitKey(1) == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()
