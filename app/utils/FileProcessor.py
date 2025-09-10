import pandas as pd
import io
from typing import List, Dict, Any, Tuple
from fastapi import UploadFile, HTTPException
import logging

logger = logging.getLogger(__name__)


class FileProcessor:
    
    REQUIRED_COLUMNS = ['name', 'country_code', 'phone_number']
    OPTIONAL_COLUMNS = ['allow_broadcast', 'allow_sms', 'source']
    
    @classmethod
    async def process_file(cls, file: UploadFile) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:

        try:
            content = await file.read()
            
            await file.seek(0)
            
            if not file.filename:
                raise HTTPException(status_code=400, detail="No filename provided")
            
            if file.filename.lower().endswith(('.xlsx', '.xls')):
                df = cls._read_excel_file(content)
            elif file.filename.lower().endswith('.csv'):
                df = cls._read_csv_file(content)
            else:
                raise HTTPException(
                    status_code=400, 
                    detail="Unsupported file format. Please upload Excel (.xlsx, .xls) or CSV files only."
                )
            
            return cls._process_dataframe(df)
            
        except pd.errors.EmptyDataError:
            raise HTTPException(status_code=400, detail="The uploaded file is empty")
        except pd.errors.ParserError as e:
            raise HTTPException(status_code=400, detail=f"Error parsing file: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")
    
    @classmethod
    def _read_excel_file(cls, content: bytes) -> pd.DataFrame:
        return pd.read_excel(io.BytesIO(content))
    
    @classmethod
    def _read_csv_file(cls, content: bytes) -> pd.DataFrame:
        return pd.read_csv(io.StringIO(content.decode('utf-8')))
    
    @classmethod
    def _process_dataframe(cls, df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:

        if df.empty:
            raise HTTPException(status_code=400, detail="The uploaded file contains no data")
        
        missing_columns = [col for col in cls.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_columns)}. Required columns are: {', '.join(cls.REQUIRED_COLUMNS)}"
            )
        
        valid_records = []
        invalid_records = []
        
        for index, row in df.iterrows():
            try:
                record = cls._process_row(row, index + 2)  # +2 because pandas is 0-indexed and we account for header
                valid_records.append(record)
            except ValueError as e:
                invalid_records.append({
                    'row': index + 2,
                    'error': str(e),
                    'data': row.to_dict()
                })
        
        return valid_records, invalid_records
    
    @classmethod
    def _process_row(cls, row: pd.Series, row_number: int) -> Dict[str, Any]:

        record = {}
        
        for col in cls.REQUIRED_COLUMNS:
            value = row[col]
            
            if pd.isna(value) or (isinstance(value, str) and value.strip() == ''):
                raise ValueError(f"Required field '{col}' is empty or missing")
            
            if col == 'name':
                record[col] = str(value).strip()
                if not record[col]:
                    raise ValueError(f"Name cannot be empty")
            elif col == 'country_code':
                country_code = str(value).strip()
                if not country_code.startswith('+'):
                    country_code = '+' + country_code
                record[col] = country_code
            elif col == 'phone_number':
                phone_number = str(value).strip()
                phone_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')
                if not phone_number:
                    raise ValueError(f"Invalid phone number format")
                record[col] = phone_number
        
        for col in cls.OPTIONAL_COLUMNS:
            if col in row and not pd.isna(row[col]):
                if col in ['allow_broadcast', 'allow_sms']:
                    value = row[col]
                    if isinstance(value, str):
                        record[col] = value.lower() in ['true', 'yes', '1', 'y']
                    elif isinstance(value, bool):
                        record[col] = value
                    elif isinstance(value, (int, float)):
                        record[col] = bool(value)
                    else:
                        record[col] = True
                elif col == 'source':
                    record[col] = str(row[col]).strip() if not pd.isna(row[col]) else 'whatsapp'
            else:
                if col in ['allow_broadcast', 'allow_sms']:
                    record[col] = True
                elif col == 'source':
                    record[col] = 'whatsapp'
        
        return record