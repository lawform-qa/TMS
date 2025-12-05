"""
리포트 생성 서비스
"""
import pandas as pd
from io import BytesIO
from datetime import datetime
from models import db, TestCase
from sqlalchemy import func
from utils.logger import get_logger

logger = get_logger(__name__)


class ReportService:
    """리포트 생성 관련 비즈니스 로직"""
    
    @staticmethod
    def generate_test_summary_report(report_type='excel'):
        """테스트 요약 리포트 생성"""
        from services.testcase_service import TestCaseService
        
        summary_data = TestCaseService.get_testcase_statistics()
        
        if report_type == 'excel':
            return ReportService._generate_excel_report(summary_data)
        else:
            raise ValueError('지원하지 않는 리포트 타입입니다')
    
    @staticmethod
    def _generate_excel_report(summary_data):
        """Excel 리포트 생성"""
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 환경별 통계 시트
            env_df = pd.DataFrame(summary_data['environment_stats'])
            env_df.to_excel(writer, sheet_name='Environment_Stats', index=False)
            
            # 카테고리별 통계 시트
            cat_df = pd.DataFrame(summary_data['category_stats'])
            cat_df.to_excel(writer, sheet_name='Category_Stats', index=False)
            
            # 자동화 통계 시트
            automation_df = pd.DataFrame([summary_data['automation_stats']])
            automation_df.to_excel(writer, sheet_name='Automation_Stats', index=False)
        
        output.seek(0)
        
        return output, f'test_summary_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

