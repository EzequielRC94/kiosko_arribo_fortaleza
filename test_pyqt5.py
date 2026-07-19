import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget

print("PyQt5 cargado exitosamente.")

app = QApplication(sys.argv)
ventana = QWidget()
ventana.setWindowTitle('Control de Auto Arribo')
ventana.setGeometry(100, 100, 300, 200)

etiqueta = QLabel('¡Sistema Activo!', parent=ventana)
etiqueta.move(100, 80)

ventana.show()
sys.exit(app.exec_())
