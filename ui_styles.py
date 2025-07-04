class UIStyles:
    @staticmethod
    def get_stylesheet():
        return """
        /* Main Window */
        QMainWindow {
            background-color: #F5F5F5;
            color: #2C3E50;
        }
        
        /* Header */
        QLabel#header {
            font-size: 24px;
            font-weight: bold;
            color: #2C3E50;
            margin: 0px 0px 20px 0px;
            padding: 10px;
        }
        
        /* Tab Widget */
        QTabWidget {
            background-color: white;
            border: none;
        }
        
        QTabWidget::pane {
            border: 1px solid #BDC3C7;
            background-color: white;
        }
        
        QTabBar::tab {
            background-color: #ECF0F1;
            color: #2C3E50;
            padding: 10px 15px;
            margin-right: 2px;
            font-weight: 600;
            font-size: 14px;
        }
        
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 2px solid #3498DB;
        }
        
        QTabBar::tab:hover {
            background-color: #D5DBDB;
        }
        
        /* Tab Titles */
        QLabel#tab-title {
            font-size: 18px;
            font-weight: 600;
            color: #2C3E50;
            margin: 0px 0px 10px 0px;
        }
        
        /* Descriptions */
        QLabel#description {
            color: #7F8C8D;
            margin: 0px 0px 20px 0px;
            font-size: 14px;
        }
        
        /* Console/Output Areas */
        QTextEdit#console {
            background-color: #2C3E50;
            color: #ECF0F1;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            border: 1px solid #34495E;
            padding: 10px;
            line-height: 1.4;
        }
        
        /* Buttons */
        QPushButton {
            font-weight: 600;
            font-size: 14px;
            padding: 8px 15px;
            border: none;
            border-radius: 4px;
            min-width: 120px;
        }
        
        QPushButton#primary-button {
            background-color: #3498DB;
            color: white;
        }
        
        QPushButton#primary-button:hover {
            background-color: #2980B9;
        }
        
        QPushButton#primary-button:pressed {
            background-color: #21618C;
        }
        
        QPushButton#success-button {
            background-color: #27AE60;
            color: white;
        }
        
        QPushButton#success-button:hover {
            background-color: #229954;
        }
        
        QPushButton#success-button:pressed {
            background-color: #1E8449;
        }
        
        QPushButton#danger-button {
            background-color: #E74C3C;
            color: white;
        }
        
        QPushButton#danger-button:hover {
            background-color: #C0392B;
        }
        
        QPushButton#danger-button:pressed {
            background-color: #A93226;
        }
        
        QPushButton#warning-button {
            background-color: #F39C12;
            color: white;
        }
        
        QPushButton#warning-button:hover {
            background-color: #E67E22;
        }
        
        QPushButton#warning-button:pressed {
            background-color: #D35400;
        }
        
        QPushButton#info-button {
            background-color: #16A085;
            color: white;
        }
        
        QPushButton#info-button:hover {
            background-color: #138D75;
        }
        
        QPushButton#info-button:pressed {
            background-color: #117A65;
        }
        
        QPushButton:disabled {
            background-color: #BDC3C7;
            color: #7F8C8D;
        }
        
        /* ComboBox */
        QComboBox {
            padding: 5px 10px;
            border: 1px solid #BDC3C7;
            border-radius: 4px;
            background-color: white;
            min-width: 100px;
        }
        
        QComboBox:hover {
            border-color: #3498DB;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #7F8C8D;
            margin-right: 5px;
        }
        
        /* Labels */
        QLabel {
            color: #2C3E50;
        }
        
        /* Scrollbars */
        QScrollBar:vertical {
            background-color: #34495E;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #7F8C8D;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #95A5A6;
        }
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }

        /* Network Tools Specific Styles */
        QGroupBox {
            font-weight: bold;
            border: 2px solid #BDC3C7;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #2C3E50;
        }

        QTableWidget {
            gridline-color: #BDC3C7;
            background-color: white;
            alternate-background-color: #F8F9FA;
        }

        QTableWidget::item {
            padding: 5px;
            border-bottom: 1px solid #ECF0F1;
        }

        QTableWidget::item:selected {
            background-color: #3498DB;
            color: white;
        }

        QHeaderView::section {
            background-color: #34495E;
            color: white;
            padding: 8px;
            border: none;
            font-weight: bold;
        }

        QLineEdit {
            padding: 5px 10px;
            border: 1px solid #BDC3C7;
            border-radius: 4px;
            background-color: white;
            font-size: 14px;
        }

        QLineEdit:focus {
            border-color: #3498DB;
            outline: none;
        }

        QSpinBox {
            padding: 5px;
            border: 1px solid #BDC3C7;
            border-radius: 4px;
            background-color: white;
        }

        QCheckBox {
            spacing: 5px;
            color: #2C3E50;
        }

        QCheckBox::indicator {
            width: 18px;
            height: 18px;
        }

        QCheckBox::indicator:unchecked {
            border: 2px solid #BDC3C7;
            background-color: white;
            border-radius: 3px;
        }

        QCheckBox::indicator:checked {
            border: 2px solid #27AE60;
            background-color: #27AE60;
            border-radius: 3px;
        }

        QProgressBar {
            border: 1px solid #BDC3C7;
            border-radius: 4px;
            text-align: center;
            font-weight: bold;
        }

        QProgressBar::chunk {
            background-color: #3498DB;
            border-radius: 3px;
        }
        """
