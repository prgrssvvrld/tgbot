from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont  
import datetime
import os

def register_russian_font():
    """Регистрирует русский шрифт для PDF"""
    try:
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",  
            "C:/Windows/Fonts/times.ttf",  
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",  
            "/System/Library/Fonts/Arial.ttf"  
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Arial', font_path))
                return 'Arial'
        
        return 'Helvetica'
    except:
        return 'Helvetica'

def generate_pdf_report():
    """Генерирует PDF отчет по событиям за сегодня"""
    from bot.database import get_events_for_today
    
    events = get_events_for_today()
    
    font_name = register_russian_font()
    
    filename = f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        alignment=1,  
        spaceAfter=30,
        fontName=font_name 
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontName=font_name  
    )
    
    elements = []
    
    title = Paragraph("ОТЧЕТ ПО СОБЫТИЯМ", title_style)  
    elements.append(title)
    
    date_text = Paragraph(f"Дата: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}", normal_style)
    elements.append(date_text)
    elements.append(Spacer(1, 20))
    
    if not events:
        no_events = Paragraph("Событий за сегодня нет", normal_style)
        elements.append(no_events)
    else:
        table_data = [['Время', 'ФИО', 'Тип', 'Описание', 'Статус']]
        
        for event in events:
            local_time = event.timestamp + datetime.timedelta(hours=0)
            time = local_time.strftime('%H:%M')
            status = "Решено" if event.is_resolved else "Активно"  
            
            event_type_russian = {
                "stop": "Остановка",
                "breakdown": "Поломка", 
                "other": "Другое"
            }
            event_type = event_type_russian.get(event.type.value, event.type.value)
            
            table_data.append([
                time,
                event.user_fio,
                event_type,
                event.description[:30] + "..." if len(event.description) > 30 else event.description,
                status
            ])
        
        table = Table(table_data, colWidths=[30*mm, 40*mm, 30*mm, 50*mm, 30*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),  
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), font_name),  
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        total_events = len(events)
        resolved_events = len([e for e in events if e.is_resolved])
        active_events = total_events - resolved_events
        
        stats_text = f"СТАТИСТИКА: Всего: {total_events} | Активных: {active_events} | Решено: {resolved_events}"
        stats_para = Paragraph(stats_text, normal_style)
        elements.append(stats_para)
    
    doc.build(elements)
    
    return filename