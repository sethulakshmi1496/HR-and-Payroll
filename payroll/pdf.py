"""
PDF generation for payslip via ReportLab.
"""
from io import BytesIO
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)


def _money(v):
    if v is None:
        return "-"
    return f"INR {Decimal(v):,.2f}"


def build_payslip_pdf(payroll) -> bytes:
    """Returns binary PDF data for a Payroll record."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=15 * mm, bottomMargin=15 * mm,
        leftMargin=15 * mm, rightMargin=15 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'h1', parent=styles['Heading1'],
        textColor=colors.HexColor('#1a56db'), spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        'sub', parent=styles['Normal'], textColor=colors.HexColor('#475569'),
        fontSize=10, spaceAfter=10,
    )

    story = []

    # Header
    story.append(Paragraph("AEC GROUP", title_style))
    story.append(Paragraph(
        f"Payslip for {payroll.month.strftime('%B %Y')}", sub_style))

    # Employee block
    profile = payroll.profile
    info = [
        ['Employee ID', profile.employee_id, 'Name', profile.user.get_full_name()],
        ['Department', profile.department.name, 'Designation', profile.designation or '-'],
        ['Status', profile.get_probation_status_display(),
         'Account', (profile.salary_account or profile.personal_account or '-')[-12:]],
    ]
    t = Table(info, colWidths=[35 * mm, 50 * mm, 30 * mm, 65 * mm])
    t.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f8fafc')),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 8 * mm))

    # Earnings & Deductions side-by-side
    earnings = [
        ['Earnings', 'Amount'],
        ['Basic (Earned)',
         _money(Decimal(payroll.daily_rate) * Decimal(payroll.days_present))],
        [f'Overtime ({payroll.ot_hours} hr)', _money(payroll.ot_amount)],
        ['Incentives', _money(payroll.incentive_total)],
        ['', ''],
        ['Gross Salary', _money(payroll.gross_salary)],
    ]

    deductions = [
        ['Deductions', 'Amount'],
        ['Professional Tax (Kerala)', _money(payroll.pt_deduction)],
        ['ESI (Employee 0.75%)', _money(payroll.esi_deduction)],
        ['PF (12%)', _money(payroll.pf_deduction)],
        ['Other', _money(payroll.other_deductions)],
        ['Total Deductions', _money(payroll.total_deductions)],
    ]

    et = Table(earnings, colWidths=[55 * mm, 35 * mm])
    dt = Table(deductions, colWidths=[55 * mm, 35 * mm])
    common_style = TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a56db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f1f5f9')),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ])
    et.setStyle(common_style)
    dt.setStyle(common_style)

    wrapper = Table([[et, dt]], colWidths=[90 * mm, 90 * mm])
    wrapper.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(wrapper)
    story.append(Spacer(1, 8 * mm))

    # Attendance summary
    att = [
        ['Working Days', str(payroll.working_days)],
        ['Days Present', str(payroll.days_present)],
        ['Days Absent', str(payroll.days_absent)],
        ['OT Hours', str(payroll.ot_hours)],
    ]
    at = Table(att, colWidths=[50 * mm, 30 * mm])
    at.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(at)
    story.append(Spacer(1, 8 * mm))

    # Net pay banner
    net = Table([['NET PAY', _money(payroll.net_salary)]],
                colWidths=[120 * mm, 60 * mm])
    net.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0f766e')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
    ]))
    story.append(net)
    story.append(Spacer(1, 10 * mm))

    foot = ParagraphStyle('foot', parent=styles['Normal'],
                          textColor=colors.HexColor('#64748b'),
                          fontSize=8, alignment=1)
    story.append(Paragraph(
        "This is a computer-generated payslip. AEC Group HR & Payroll System.",
        foot))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
