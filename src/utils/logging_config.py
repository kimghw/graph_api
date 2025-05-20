"""로깅 설정 모듈

이 모듈은 애플리케이션의 로깅 설정을 관리합니다.
"""

import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


class LoggerFactory:
    """로거 팩토리 클래스

    애플리케이션 전체에서 사용되는 로거 인스턴스를 관리합니다.
    """

    # 로거 인스턴스를 저장하는 딕셔너리
    _loggers = {}
    
    # 기본 로그 디렉토리
    _log_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "logs"
    
    # 로그 파일 경로
    _log_file = _log_dir / "app.log"
    
    # 로그 포맷
    _log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 로그 레벨
    _log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    
    @classmethod
    def initialize(cls):
        """로깅 시스템을 초기화합니다."""
        # 로그 디렉토리가 없으면 생성
        if not cls._log_dir.exists():
            cls._log_dir.mkdir(parents=True, exist_ok=True)
        
        # 루트 로거 설정
        root_logger = logging.getLogger()
        root_logger.setLevel(cls._get_log_level())
        
        # 콘솔 핸들러 설정
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(cls._get_log_level())
        console_handler.setFormatter(cls._get_formatter())
        
        # 파일 핸들러 설정 (로그 파일 순환)
        file_handler = RotatingFileHandler(
            cls._log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setLevel(cls._get_log_level())
        file_handler.setFormatter(cls._get_formatter())
        
        # 핸들러 추가
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        # 로깅 초기화 완료 로그
        cls.get_logger(__name__).debug(f"로깅 시스템 초기화 완료 (레벨: {cls._log_level})")
    
    @classmethod
    def get_logger(cls, name):
        """지정된 이름의 로거 인스턴스를 반환합니다.
        
        Args:
            name (str): 로거 이름
            
        Returns:
            logging.Logger: 로거 인스턴스
        """
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(cls._get_log_level())
            cls._loggers[name] = logger
            
            # 로거 최초 생성 시 초기화 상태 확인
            if not logger.handlers and not logging.getLogger().handlers:
                cls.initialize()
                
        return cls._loggers[name]
    
    @classmethod
    def set_log_level(cls, level):
        """로그 레벨을 설정합니다.
        
        Args:
            level (str): 로그 레벨 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        cls._log_level = level.upper()
        log_level = cls._get_log_level()
        
        # 기존 로거 레벨 업데이트
        for logger in cls._loggers.values():
            logger.setLevel(log_level)
            
        # 핸들러 레벨 업데이트
        for handler in logging.getLogger().handlers:
            handler.setLevel(log_level)
        
        cls.get_logger(__name__).debug(f"로그 레벨 변경: {cls._log_level}")
    
    @classmethod
    def _get_formatter(cls):
        """로그 포맷터를 반환합니다.
        
        Returns:
            logging.Formatter: 로그 포맷터
        """
        return logging.Formatter(cls._log_format)
    
    @classmethod
    def _get_log_level(cls):
        """로그 레벨 문자열을 logging 모듈의 레벨 상수로 변환합니다.
        
        Returns:
            int: logging 모듈의 레벨 상수
        """
        return getattr(logging, cls._log_level, logging.INFO)


# 모듈 임포트 시 자동으로 초기화
LoggerFactory.initialize()
