import os
from pathlib import Path
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.lib.enums import TA_CENTER, TA_LEFT

class PDFReportGenerator:
    """Generates professional PDF reports for resume fraud analysis"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Define custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            leading=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#4f46e5'),
            spaceBefore=15,
            spaceAfter=10,
            borderPadding=(0, 0, 5, 0),
            borderWidth=1,
            borderColor=colors.HexColor('#e5e7eb')
        ))
        
        self.styles.add(ParagraphStyle(
            name='RiskBadge',
            fontSize=14,
            alignment=TA_CENTER,
            textColor=colors.white,
            backColor=colors.HexColor('#ef4444'),
            borderPadding=5,
            borderRadius=5
        ))
        
    def generate_report(self, analysis_data: dict, output_filename: str) -> str:
        """
        Generate PDF report from analysis data
        
        Args:
            analysis_data: Dictionary containing analysis results
            output_filename: Name of the output PDF file
            
        Returns:
            Path to generated PDF file
        """
        filepath = self.output_dir / output_filename
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )
        
        story = []
        results = analysis_data['fraud_results']
        
        # 1. Header
        story.append(Paragraph("Resume Verification Report", self.styles['ReportTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # 2. File Info Table
        file_info = [
            ['File Name:', analysis_data['original_filename']],
            ['Analysis ID:', analysis_data['id']],
            ['Date:', datetime.fromisoformat(analysis_data['upload_time']).strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        t = Table(file_info, colWidths=[1.5*inch, 4.5*inch])
        t.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#6b7280')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*inch))
        
        # 3. Overall Score Section (High Level Assessment)
        story.append(Paragraph("Fraud Risk Assessment", self.styles['SectionHeader']))
        
        # Determine colors based on risk
        risk_color = colors.HexColor('#10b981') # Low (Green)
        if results['risk_category'] == 'High Risk':
            risk_color = colors.HexColor('#ef4444') # Red
        elif results['risk_category'] == 'Medium Risk':
            risk_color = colors.HexColor('#f59e0b') # Amber
            
        # Score and Category Table
        score_data = [
            [
                Paragraph(f"<font size=36 color='{risk_color.hexval()}'><b>{results['fraud_score']}</b></font><br/><font size=10>FRAUD SCORE</font>", self.styles['Normal']),
                Paragraph(f"<font size=14><b>{results['risk_category']}</b></font><br/><font size=10 color='#6b7280'>RISK LEVEL</font>", self.styles['Normal']),
                Paragraph(f"<font size=14><b>{results['ml_confidence']}%</b></font><br/><font size=10 color='#6b7280'>CONFIDENCE</font>", self.styles['Normal'])
            ]
        ]
        
        t_score = Table(score_data, colWidths=[2*inch, 2*inch, 2*inch])
        t_score.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e5e7eb')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
            ('TOPPADDING', (0,0), (-1,-1), 15),
            ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ]))
        story.append(t_score)
        story.append(Spacer(1, 0.3*inch))
        
        # 4. Component Scores
        story.append(Paragraph("Component Analysis", self.styles['SectionHeader']))
        
        comp_scores = results['component_scores']
        comp_data = [
            ['Timeline Analysis', f"{comp_scores.get('timeline_score', 0)}/100"],
            ['Credential Verification', f"{comp_scores.get('credential_score', 0)}/100"],
            ['Language Pattern', f"{comp_scores.get('language_score', 0)}/100"],
            ['Anomaly Detection', f"{comp_scores.get('anomaly_score', 0)}/100"]
        ]
        
        t_comp = Table(comp_data, colWidths=[4*inch, 2*inch])
        t_comp.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f9fafb')),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_comp)
        story.append(Spacer(1, 0.3*inch))
        
        # 5. Red Flags
        story.append(Paragraph(f"Red Flags Detected ({len(results['red_flags'])})", self.styles['SectionHeader']))
        
        if not results['red_flags']:
            story.append(Paragraph("No significant red flags detected.", self.styles['Normal']))
        else:
            for flag in results['red_flags']:
                # Severity Color
                sev_color = colors.black
                if flag['severity'] == 'Critical': sev_color = colors.red
                elif flag['severity'] == 'High': sev_color = colors.orange
                
                flag_text = f"""
                <b><font color="{sev_color.hexval()}">[{flag['severity']}] {flag['category']}</font></b><br/>
                {flag['description']}<br/>
                <i>Recommendation: {flag.get('recommendation', 'Review manually')}</i>
                """
                story.append(Paragraph(flag_text, self.styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
        
        story.append(Spacer(1, 0.2*inch))
        
        # 6. Recommendations
        story.append(Paragraph("Recommendations", self.styles['SectionHeader']))
        
        if not results['recommendations']:
            story.append(Paragraph("No specific recommendations generated.", self.styles['Normal']))
        else:
            for rec in results['recommendations']:
                story.append(Paragraph(f"• {rec}", self.styles['Normal']))
                
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_text = Paragraph(
            f"Generated by AI-Powered Resume Fraud Detection System on {datetime.now().strftime('%Y-%m-%d')}", 
            ParagraphStyle('Footer', parent=self.styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
        )
        story.append(footer_text)
        
        # Build PDF
        doc.build(story)
        return str(filepath)

if __name__ == "__main__":
    # Test
    generator = PDFReportGenerator(Path('.'))
    # Dummy data test would go here
