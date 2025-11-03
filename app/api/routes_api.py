"""
🎯 Mock API 엔드포인트
시니어의 설명:
- 실제 백엔드 완성 전까지 사용할 가짜 데이터
- 프론트엔드 개발 시 유용
- 나중에 실제 DB로 교체
"""

from fastapi import APIRouter, Query, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
from collections import Counter
import random
import time
import httpx

router = APIRouter(tags=["api"])

# Ethics Analyzer 전역 변수 (main.py에서 초기화됨)
ethics_analyzer = None

# ============================================
# 📊 데이터 모델 (Pydantic)
# ============================================

class SearchResult(BaseModel):
    """검색 결과 모델"""
    id: int
    title: str
    content: str
    author: str
    date: str
    category: str

class BounceMetrics(BaseModel):
    """이탈률 메트릭"""
    avg_bounce_rate: float
    total_visitors: int
    bounced_visitors: int
    period: str

class TrendItem(BaseModel):
    """트렌드 아이템"""
    keyword: str
    mentions: int
    change: float
    category: str

class ReportCategory(BaseModel):
    """신고 카테고리"""
    name: str
    count: int
    status: str
    avg_processing_time: str

class EthicsScoreRequest(BaseModel):
    """비윤리/스팸지수 분석 요청"""
    text: str

class EthicsScoreResponse(BaseModel):
    """비윤리/스팸지수 분석 응답"""
    ethics_score: float
    detected_expressions: List[dict]
    recommendations: List[dict]

# ============================================
# 🔍 검색 API
# ============================================

@router.get("/search")
async def search(q: str = Query(..., description="검색 키워드")):
    """
    자연어 검색 API
    
    **시니어의 팁:**
    - Query(...) : 필수 파라미터
    - Query(None) : 선택적 파라미터
    """
    
    if not q:
        raise HTTPException(status_code=400, detail="검색어를 입력하세요")
    
    # Mock 데이터 생성
    results = [
        {
            "id": i,
            "title": f"{q}에 관한 게시글 {i+1}",
            "content": f"이것은 '{q}' 키워드와 관련된 샘플 게시글입니다. 실제로는 데이터베이스에서 검색됩니다.",
            "author": f"사용자{random.randint(1, 100)}",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "category": random.choice(["자유게시판", "질문", "정보", "토론"])
        }
        for i in range(5)
    ]
    
    return {
        "query": q,
        "total": len(results),
        "results": results
    }

# ============================================
# 📊 이탈률 메트릭 API
# ============================================

@router.get("/metrics/bounce")
async def get_bounce_metrics():
    """
    방문객 이탈률 데이터
    
    **Mock 데이터:**
    실제로는 Google Analytics나 자체 분석 시스템에서 가져옴
    """
    
    return {
        "metrics": {
            "avg_bounce_rate": 42.5,
            "total_visitors": 15234,
            "bounced_visitors": 6474,
            "period": "2025-01-01 ~ 2025-01-31"
        },
        "details": [
            {
                "date": f"2025-01-{i+1:02d}",
                "visitors": random.randint(300, 800),
                "bounced": random.randint(100, 400),
                "bounce_rate": random.uniform(30, 60)
            }
            for i in range(7)
        ]
    }

# ============================================
# 📈 트렌드 분석 API (실제 데이터)
# ============================================

@router.get("/trends")
async def get_trends(limit: int = Query(100, ge=1, le=1000)):
    """
    실제 트렌드 데이터 반환 (dad.dothome.co.kr API 연동)
    
    **시니어의 설명:**
    - 외부 API에서 실제 인기 검색어 데이터를 가져옴
    - 키워드 정규화 (검색했음→검색, 검색어→검색)
    - 날짜별 타임라인 생성
    - 실제 증감률 계산
    """
    
    # ⭐ 키워드 정규화 매핑 (자연어 → 키워드)
    KEYWORD_NORMALIZATION = {
        "검색했음": "검색",
        "검색하기": "검색",
        "검색중": "검색",
        "검색어": "검색",
        "검색어들": "검색",
        "안녕하세요": "인사",
        "안녕": "인사",
        "ㅎㅇ": "인사",
    }
    
    def normalize_keyword(word: str) -> str:
        """키워드 정규화"""
        word = word.strip()
        return KEYWORD_NORMALIZATION.get(word, word)
    
    try:
        print(f"\n[DEBUG] Calling dad.dothome.co.kr API with limit={limit}")
        async with httpx.AsyncClient(timeout=10.0) as client:
            # ✅ 1. 실제 인기 검색어 API 호출 (standalone 버전)
            url = "https://dad.dothome.co.kr/adm/popular_api_standalone.php"
            print(f"[DEBUG] URL: {url}")
            
            response = await client.get(url, params={"limit": limit})
            print(f"[DEBUG] Response status: {response.status_code}")
            print(f"[DEBUG] Response content-type: {response.headers.get('content-type')}")
            
            response.raise_for_status()
            
            data = response.json()
            print(f"[DEBUG] JSON parsed successfully")
            print(f"[DEBUG] success={data.get('success')}, data_count={len(data.get('data', []))}")
            
            if not data.get("success", False):
                raise Exception("API returned error")
            
            # ✅ 2. 게시글/댓글 통계 API 호출
            stats_url = "https://dad.dothome.co.kr/adm/board_stats_api.php"
            print(f"[DEBUG] Fetching board stats from: {stats_url}")
            
            stats_response = await client.get(stats_url)
            stats_data = stats_response.json()
            
            total_posts = 0
            total_comments = 0
            
            if stats_data.get("success"):
                total_posts = stats_data["data"]["total_posts"]
                total_comments = stats_data["data"]["total_comments"]
                print(f"[DEBUG] Board stats: posts={total_posts}, comments={total_comments}")
                
                # 디버그 정보 출력
                if "debug" in stats_data:
                    print(f"[DEBUG] Tables found: {stats_data['debug'].get('tables_found', [])}")
            else:
                print(f"[DEBUG] Board stats API failed, using defaults")
            
            # 데이터 변환
            api_data = data.get("data", [])
            print(f"[DEBUG] Converting {len(api_data)} items to keywords")
            
            # ⭐ 키워드 정규화 + 빈도 집계
            word_counts = Counter()
            date_word_counts = {}  # 날짜별 키워드 빈도
            
            for item in api_data:
                word = item.get("word", "").strip()
                date = item.get("date", "")
                
                if word:
                    # 키워드 정규화
                    normalized_word = normalize_keyword(word)
                    word_counts[normalized_word] += 1
                    
                    # 날짜별 집계
                    if date not in date_word_counts:
                        date_word_counts[date] = Counter()
                    date_word_counts[date][normalized_word] += 1
            
            # 빈도순으로 정렬하여 키워드 생성
            keywords = [
                {
                    "word": word,
                    "count": count
                }
                for word, count in word_counts.most_common()
            ]
            
            print(f"[DEBUG] Top 5 keywords (after normalization): {keywords[:5]}")
            
            # ⭐ 증감률 계산 (날짜별 비교)
            dates = sorted(date_word_counts.keys())
            trends = []
            
            for kw in keywords[:10]:
                word = kw["word"]
                
                # 최근 날짜와 이전 날짜의 검색 횟수 비교
                if len(dates) >= 2:
                    recent_count = date_word_counts[dates[-1]].get(word, 0)
                    previous_count = date_word_counts[dates[-2]].get(word, 0)
                    
                    if previous_count > 0:
                        change = ((recent_count - previous_count) / previous_count) * 100
                    else:
                        change = 100.0 if recent_count > 0 else 0.0
                else:
                    change = 0.0
                
                # 카테고리 자동 분류
                if change > 50:
                    category = "급상승"
                elif change > 0:
                    category = "상승"
                elif change < -50:
                    category = "급감"
                elif change < 0:
                    category = "하락"
                else:
                    category = "유지"
                
                trends.append({
                    "keyword": word,
                    "mentions": kw["count"],
                    "change": round(change, 1),
                    "category": category
                })
            
            # ⭐ 타임라인 데이터 생성 (날짜별 검색 횟수)
            timeline = []
            for date in sorted(dates):
                total_count = sum(date_word_counts[date].values())
                timeline.append({
                    "date": date,
                    "count": total_count
                })
            
            # ⭐ 실제 통계 계산
            total_searches = sum(word_counts.values())
            unique_keywords = len(keywords)
            
            return {
                "summary": {
                    "total_posts": total_posts,             # ⭐ 실제 게시글 수
                    "total_comments": total_comments,        # ⭐ 실제 댓글 수
                    "total_searches": total_searches,        # 총 검색 횟수
                    "unique_keywords": unique_keywords,      # 고유 키워드 수
                    "total_trends": len(keywords),
                    "new_trends": len([t for t in trends if t["change"] > 50]),
                    "rising_trends": len([t for t in trends if t["change"] > 0])
                },
                "keywords": keywords,
                "trends": trends,
                "timeline": timeline,  # ⭐ 타임라인 데이터 추가!
                "source": "dad.dothome.co.kr",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        # ⭐ 에러 발생 시 현실적인 Mock 데이터 반환 (로그인 문제 대응)
        print(f"[INFO] Using mock data due to: {e}")
        
        # 현실적인 한국어 키워드 Mock 데이터
        mock_keywords_pool = [
            "인공지능", "ChatGPT", "블록체인", "메타버스", "NFT",
            "빅데이터", "클라우드", "사이버보안", "딥러닝", "머신러닝",
            "자율주행", "전기차", "테슬라", "삼성전자", "반도체",
            "K-POP", "BTS", "축구", "야구", "배구",
            "주식", "비트코인", "부동산", "금리", "환율",
            "날씨", "미세먼지", "코로나", "백신", "건강",
            "다이어트", "운동", "요가", "필라테스", "헬스",
            "맛집", "카페", "여행", "제주도", "부산",
            "넷플릭스", "유튜브", "인스타그램", "틱톡", "페이스북",
            "아이폰", "갤럭시", "게임", "LOL", "오버워치",
            "영화", "드라마", "예능", "웹툰", "만화",
            "패션", "뷰티", "화장품", "스킨케어", "메이크업",
            "부동산", "전세", "월세", "아파트", "오피스텔",
            "취업", "이직", "연봉", "면접", "자소서"
        ]
        
        # 랜덤하게 limit개 선택하고 실제같은 빈도 부여
        selected_keywords = random.sample(
            mock_keywords_pool, 
            min(limit, len(mock_keywords_pool))
        )
        
        # 실제같은 검색 빈도 생성 (높은 빈도 ~ 낮은 빈도)
        keywords = [
            {
                "word": kw,
                "count": random.randint(1, 15)  # 현실적인 검색 횟수 (1~15회)
            }
            for kw in selected_keywords
        ]
        
        # 빈도순으로 정렬
        keywords.sort(key=lambda x: x["count"], reverse=True)
        
        # 상위 10개로 트렌드 생성
        trends = [
            {
                "keyword": kw["word"],
                "mentions": kw["count"],  # ⭐ count와 동일하게!
                "change": random.uniform(-30, 50),
                "category": random.choice(["인기", "트렌드", "이슈", "급상승", "화제"])
            }
            for kw in keywords[:10]
        ]
        
        return {
            "summary": {
                "total_trends": len(keywords),
                "new_trends": len([t for t in trends if t["change"] > 20]),
                "rising_trends": len([t for t in trends if t["change"] > 0])
            },
            "keywords": keywords,
            "trends": trends,
            "source": "mock_data",
            "note": "API 인증 문제로 Mock 데이터 사용 중",
            "timestamp": datetime.now().isoformat()
        }

# ============================================
# 🚨 신고글 분류 API
# ============================================

@router.get("/reports/moderation")
async def get_reports():
    """신고글 통계 데이터"""
    
    categories = [
        ("스팸/광고", "pending"),
        ("욕설/비방", "resolved"),
        ("음란물", "resolved"),
        ("개인정보 노출", "pending"),
        ("저작권 침해", "rejected"),
        ("기타", "pending")
    ]
    
    total = sum(random.randint(10, 100) for _ in categories)
    
    return {
        "stats": {
            "total": total,
            "pending": random.randint(20, 50),
            "resolved": random.randint(30, 60),
            "rejected": random.randint(5, 15)
        },
        "categories": [
            {
                "name": name,
                "count": random.randint(10, 100),
                "status": status,
                "avg_processing_time": f"{random.randint(1, 48)}시간"
            }
            for name, status in categories
        ]
    }

# ============================================
# ⚠️ 비윤리/스팸지수 분석 API
# ============================================

@router.post("/moderation/ethics-score")
async def analyze_ethics_score(request: EthicsScoreRequest):
    """
    텍스트 비윤리/스팸지수 분석
    
    **실제로는:**
    - NLP 모델 사용
    - AI 기반 분석
    - 데이터베이스 저장
    """
    
    text = request.text.strip()
    
    if not text:
        raise HTTPException(status_code=400, detail="분석할 텍스트를 입력하세요")
    
    # 간단한 키워드 기반 Mock 분석
    ethics_keywords = ["바보", "멍청", "쓰레기", "죽어", "꺼져"]
    detected = []
    
    for keyword in ethics_keywords:
        if keyword in text:
            detected.append({
                "text": keyword,
                "type": "비윤리적 표현",
                "severity": "high" if len(keyword) > 2 else "medium"
            })
    
    ethics_score = min(len(detected) * 25, 100)
    
    recommendations = []
    if ethics_score >= 70:
        recommendations.append({
            "priority": "high",
            "message": "심각한 비윤리적 표현이 감지되었습니다. 즉시 조치가 필요합니다."
        })
    elif ethics_score >= 40:
        recommendations.append({
            "priority": "medium",
            "message": "부적절한 표현이 포함되어 있습니다. 검토가 필요합니다."
        })
    else:
        recommendations.append({
            "priority": "low",
            "message": "특별한 문제가 발견되지 않았습니다."
        })
    
    return {
        "ethics_score": ethics_score,
        "detected_expressions": detected,
        "recommendations": recommendations
    }

# ============================================
# 📊 대시보드 통계 API
# ============================================

@router.get("/dashboard/stats")
async def get_dashboard_stats():
    """대시보드용 실시간 통계"""
    
    return {
        "users": {
            "total": 12345,
            "active": 1234,
            "new_today": 56
        },
        "posts": {
            "total": 45678,
            "today": 234
        },
        "reports": {
            "total": 234,
            "pending": 45
        },
        "system": {
            "uptime": "99.9%",
            "response_time": "120ms",
            "status": "healthy"
        }
    }

# ============================================
# 🧪 테스트 엔드포인트
# ============================================

@router.get("/test")
async def test_api():
    """API 연결 테스트"""
    return {
        "status": "success",
        "message": "API가 정상적으로 작동하고 있습니다!",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@router.get("/test/error")
async def test_error():
    """에러 테스트"""
    raise HTTPException(status_code=500, detail="테스트용 에러입니다")

# ============================================
# 🛡️ Ethics 비윤리/스팸 분석 API (실제 구현)
# ============================================

class EthicsAnalyzeRequest(BaseModel):
    """Ethics 분석 요청 모델"""
    text: str = Field(..., description="분석할 텍스트", min_length=1, max_length=1000)
    
    class Config:
        schema_extra = {
            "example": {
                "text": "너 정말 멍청하구나"
            }
        }

class EthicsAnalyzeResponse(BaseModel):
    """Ethics 분석 응답 모델"""
    text: str
    score: float = Field(..., description="비윤리 점수 (0-100)")
    confidence: float = Field(..., description="비윤리 신뢰도 (0-100)")
    spam: float = Field(..., description="스팸 지수 (0-100)")
    spam_confidence: float = Field(..., description="스팸 신뢰도 (0-100)")
    types: List[str] = Field(..., description="분석 유형 목록")


def simplify_result(result: dict) -> dict:
    """분석 결과를 간결한 형식으로 변환 (소수점 1자리)"""
    return {
        'text': result['text'],
        'score': round(result['final_score'], 1),
        'confidence': round(result['final_confidence'], 1),
        'spam': round(result['spam_score'], 1),
        'spam_confidence': round(result['spam_confidence'], 1),
        'types': result['types']
    }


@router.post("/ethics/analyze", response_model=EthicsAnalyzeResponse, tags=["ethics"])
async def ethics_analyze(request_data: EthicsAnalyzeRequest, request: Request):
    """
    텍스트 비윤리/스팸 분석 (하이브리드 시스템)
    
    - **text**: 분석할 텍스트 (최대 1000자)
    
    Returns:
    - 비윤리 점수, 신뢰도, 스팸 지수, 유형 정보 등
    """
    global ethics_analyzer
    
    # 지연 로딩: 서버 시작 시 초기화 실패한 경우 재시도
    if ethics_analyzer is None:
        try:
            print("[INFO] Ethics 분석기 초기화 중 (재시도)...")
            from ethics.ethics_hybrid_predictor import HybridEthicsAnalyzer
            ethics_analyzer = HybridEthicsAnalyzer()
            print("[INFO] Ethics 분석기 초기화 완료")
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"분석기 초기화 실패: {str(e)}. models/ 디렉토리와 .env 파일을 확인하세요.")
    
    if ethics_analyzer is None:
        raise HTTPException(status_code=503, detail="분석기가 초기화되지 않았습니다.")
    
    start_time = time.time()
    
    try:
        result = ethics_analyzer.analyze(request_data.text)
        simplified = simplify_result(result)
        
        # 응답 시간 계산
        response_time = time.time() - start_time
        
        # 로그 저장
        try:
            from ethics.ethics_db_logger import db_logger
            db_logger.log_analysis(
                text=simplified['text'],
                score=simplified['score'],
                confidence=simplified['confidence'],
                spam=simplified['spam'],
                spam_confidence=simplified['spam_confidence'],
                types=simplified['types'],
                ip_address=request.client.host,
                user_agent=request.headers.get('user-agent'),
                response_time=response_time
            )
        except Exception as log_error:
            print(f"[WARN] 로그 저장 실패: {log_error}")
        
        return simplified
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")


@router.get("/ethics/logs", tags=["ethics"])
async def get_ethics_logs(
    limit: int = Query(100, description="최대 조회 개수"),
    offset: int = Query(0, description="시작 위치"),
    min_score: Optional[float] = Query(None, description="최소 점수 필터"),
    max_score: Optional[float] = Query(None, description="최대 점수 필터"),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)")
):
    """
    Ethics 분석 로그 조회
    
    - **limit**: 최대 조회 개수 (기본값: 100)
    - **offset**: 시작 위치 (기본값: 0)
    - **min_score**: 최소 점수 필터
    - **max_score**: 최대 점수 필터
    - **start_date**: 시작 날짜 (YYYY-MM-DD)
    - **end_date**: 종료 날짜 (YYYY-MM-DD)
    """
    try:
        from ethics.ethics_db_logger import db_logger
        logs = db_logger.get_logs(
            limit=limit,
            offset=offset,
            min_score=min_score,
            max_score=max_score,
            start_date=start_date,
            end_date=end_date
        )
        return {
            "logs": logs,
            "count": len(logs),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그 조회 중 오류: {str(e)}")


@router.get("/ethics/logs/stats", tags=["ethics"])
async def get_ethics_statistics(days: int = Query(7, description="조회할 일수")):
    """
    Ethics 통계 정보 조회
    
    - **days**: 조회할 일수 (기본값: 7일)
    
    Returns:
    - 전체 건수, 평균 점수, 고위험 건수, 스팸 건수, 일별 통계
    """
    try:
        from ethics.ethics_db_logger import db_logger
        stats = db_logger.get_statistics(days=days)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류: {str(e)}")


@router.delete("/ethics/logs/{log_id}", tags=["ethics"])
async def delete_ethics_log(log_id: int):
    """
    특정 Ethics 로그 삭제
    
    - **log_id**: 삭제할 로그의 ID
    
    Returns:
    - 삭제 성공 메시지
    """
    try:
        from ethics.ethics_db_logger import db_logger
        success = db_logger.delete_log(log_id)
        if success:
            return {
                "success": True,
                "message": f"로그 ID {log_id} 삭제 완료"
            }
        else:
            raise HTTPException(status_code=404, detail="해당 로그를 찾을 수 없습니다")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그 삭제 중 오류: {str(e)}")


@router.delete("/ethics/logs/batch/old", tags=["ethics"])
async def delete_old_ethics_logs(days: int = Query(90, description="보관 기간 (일)")):
    """
    오래된 Ethics 로그 삭제
    
    - **days**: 보관 기간 (기본값: 90일, 0이면 모든 로그 삭제)
    
    Returns:
    - 삭제된 로그 수
    """
    try:
        from ethics.ethics_db_logger import db_logger
        if days == 0:
            # 모든 로그 삭제
            deleted_count = db_logger.delete_all_logs()
            return {
                "deleted_count": deleted_count,
                "message": f"모든 로그 {deleted_count}개 삭제 완료"
            }
        else:
            # 지정된 기간 이전 로그 삭제
            deleted_count = db_logger.delete_old_logs(days=days)
            return {
                "deleted_count": deleted_count,
                "message": f"{days}일 이전 로그 {deleted_count}개 삭제 완료"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그 삭제 중 오류: {str(e)}")

# ============================================
# 🚨 이탈 징후 관리자 대시보드 API
# 이 API는 관리자 대시보드용 RAG 기반 이탈 징후 경보
# ============================================

class RiskFeedbackRequest(BaseModel):
    """위험 피드백 요청 모델"""
    chunk_id: str = Field(..., description="위험 문장 청크 ID")
    confirmed: bool = Field(..., description="관리자 확인 여부 (true: 맞다, false: 아니다)")
    
    class Config:
        schema_extra = {
            "example": {
                "chunk_id": "user123_post456_0",
                "confirmed": True
            }
        }

class RiskReportRequest(BaseModel):
    """위험 보고서 생성 요청 모델"""
    text: str = Field(..., description="분석할 게시글/댓글 텍스트")
    user_id: str = Field(..., description="작성자 사용자 ID")
    post_id: str = Field(..., description="게시글 ID")
    created_at: Optional[str] = Field(None, description="작성 시간 (ISO 형식, 선택사항)")
    
    class Config:
        schema_extra = {
            "example": {
                "text": "이 서비스 정말 싫어요. 그만두고 싶어요. 시간낭비인 것 같아서 포기할래요.",
                "user_id": "user_12345",
                "post_id": "post_67890",
                "created_at": "2025-10-31T15:30:00Z"
            }
        }

class TopRiskUser(BaseModel):
    """고위험 사용자 모델"""
    user_id: str
    username: str
    risk_score: float
    evidence_sentences: List[str]
    similar_patterns_count: int
    last_activity: str
    priority: str
    suggested_action: str
    chunk_id: str

# 임시 데모용 API - /risk/top GET 엔드포인트
@router.get("/risk/top", tags=["risk-management"])
async def get_top_risk_users(limit: int = Query(10, ge=1, le=50, description="조회할 사용자 수")):
    """
    임시 데모용 API: 최근 고위험으로 감지된 사용자/문장 Top N 조회
    
    로컬 테스트 환경에서 이탈 위험 사용자 리스트를 브라우저에서 확인할 수 있습니다.
    
    - **limit**: 조회할 사용자 수 (기본값: 10, 최대: 50)
    
    Returns:
    - 고위험 문장 리스트 (최신순 정렬)
    - 각 문장별 위험도, 사용자 정보, 확인 상태 포함
    """
    
    try:
        # 로컬 테스트용 SQLite에서 데이터 조회
        from chrun_backend.rag_pipeline.high_risk_store import init_db, get_recent_high_risk
        
        # DB 초기화 보장 (테이블 생성 및 더미 데이터 삽입)
        init_db()
        
        # 최근 고위험 문장들 조회
        high_risk_chunks = get_recent_high_risk(limit=limit)
        
        # 프론트엔드가 기대하는 구조로 변환
        users = []
        for chunk in high_risk_chunks:
            # 우선순위 결정
            risk_score = chunk.get('risk_score', 0.0)
            if risk_score >= 0.85:
                priority = "HIGH"
            elif risk_score >= 0.70:
                priority = "MEDIUM"
            else:
                priority = "LOW"
            
            # 사용자명 생성
            user_id = chunk.get('user_id', 'unknown')
            username = f"사용자_{user_id.split('_')[-1]}" if user_id != 'unknown' else "익명"
            
            user_data = {
                "user_id": user_id,
                "username": username,
                "risk_score": risk_score,
                "evidence_sentences": [chunk.get('sentence', '')],
                "similar_patterns_count": 1,
                "last_activity": chunk.get('created_at', ''),
                "priority": priority,
                "suggested_action": "관리자 검토 필요",
                "chunk_id": chunk.get('chunk_id', ''),
                "confirmed": chunk.get('confirmed', 0) == 1,
                "post_id": chunk.get('post_id')
            }
            users.append(user_data)
        
        # 통계 정보 계산
        total_users = len(users)
        high_priority_count = len([u for u in users if u["priority"] == "HIGH"])
        medium_priority_count = len([u for u in users if u["priority"] == "MEDIUM"])
        low_priority_count = len([u for u in users if u["priority"] == "LOW"])
        avg_risk_score = sum(u["risk_score"] for u in users) / total_users if total_users > 0 else 0.0
        
        return {
            "summary": {
                "total_users": total_users,
                "high_priority_count": high_priority_count,
                "medium_priority_count": medium_priority_count,
                "low_priority_count": low_priority_count,
                "avg_risk_score": round(avg_risk_score, 3),
                "last_updated": datetime.now().isoformat()
            },
            "users": users,
            "metadata": {
                "limit": limit,
                "source": "high_risk_store",
                "note": "로컬 테스트용 더미 데이터"
            }
        }
        
    except Exception as e:
        print(f"[ERROR] 고위험 사용자 조회 실패: {e}")
        return {
            "summary": {
                "total_users": 0,
                "high_priority_count": 0,
                "medium_priority_count": 0,
                "low_priority_count": 0,
                "avg_risk_score": 0.0,
                "last_updated": datetime.now().isoformat()
            },
            "users": [],
            "metadata": {
                "limit": limit,
                "source": "error",
                "error": str(e)
            }
        }

# 임시 데모용 API - /risk/feedback POST 엔드포인트
@router.post("/risk/feedback", tags=["risk-management"])
async def submit_risk_feedback(request: RiskFeedbackRequest):
    """
    임시 데모용 API: 관리자 위험 판단 피드백 제출
    
    로컬 테스트 환경에서 관리자가 위험 문장에 대한 피드백을 제출할 수 있습니다.
    
    - **chunk_id**: 위험 문장 청크 ID
    - **confirmed**: 관리자 확인 여부 (true: 맞다, false: 아니다)
    
    Returns:
    - 피드백 업데이트 결과
    """
    
    try:
        # 로컬 테스트용 SQLite에서 피드백 업데이트
        from chrun_backend.rag_pipeline.high_risk_store import update_feedback
        
        # 피드백 업데이트 실행
        update_feedback(request.chunk_id, request.confirmed)
        
        # 성공 응답 반환
        return {"status": "ok"}
            
    except Exception as e:
        print(f"[ERROR] 피드백 처리 실패: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/risk/report", tags=["risk-management"])
async def generate_risk_report(request: RiskReportRequest):
    """
    새로운 게시글/댓글에 대한 위험 보고서 생성 (관리자 전용 테스트 API)
    
    **이 API는 관리자 전용 테스트용 API입니다**
    
    새로운 게시글/댓글 텍스트를 분석하여:
    1. 문장별 이탈 위험도 점수 계산 (LLM 기반)
    2. 과거 확인된 고위험 문장들과 유사도 비교
    3. 증거 문장 및 제안 조치사항이 포함된 보고서 생성
    
    Args:
        request (RiskReportRequest): 분석 요청 데이터
            - text: 분석할 게시글/댓글 텍스트
            - user_id: 작성자 사용자 ID  
            - post_id: 게시글 ID
            - created_at: 작성 시간 (선택사항)
    
    Returns:
        Dict: 위험 보고서
            - suspicious_user_id: 의심 사용자 ID
            - evidence_sentences: 위험 문장들
            - similar_patterns: 유사한 과거 패턴들
            - why_flagged: 플래그된 이유
            - suggested_action: 제안 조치사항
            - priority: 우선순위 (HIGH/MEDIUM/LOW)
            - risk_score: 전체 위험 점수
    
    **프론트엔드 사용법:**
    ```javascript
    // 새 게시글 위험도 분석
    fetch('/api/risk/report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: '이 서비스 정말 싫어요. 그만두고 싶어요.',
        user_id: 'user_12345',
        post_id: 'post_67890'
      })
    });
    ```
    """
    
    try:
        # rag_reporter를 사용하여 위험 보고서 생성
        from chrun_backend.rag_pipeline.rag_reporter import generate_risk_report
        from datetime import datetime
        
        # created_at 파싱
        created_at = None
        if request.created_at:
            try:
                created_at = datetime.fromisoformat(request.created_at.replace('Z', '+00:00'))
            except ValueError:
                created_at = datetime.now()
        else:
            created_at = datetime.now()
        
        # 위험 보고서 생성
        report = generate_risk_report(
            new_post_text=request.text,
            user_id=request.user_id,
            post_id=request.post_id,
            created_at=created_at
        )
        
        print(f"[INFO] 위험 보고서 생성 완료: {request.user_id} / {request.post_id}")
        
        return {
            "status": "success",
            "report": report,
            "metadata": {
                "analysis_method": "rag_pipeline",
                "llm_enabled": True,
                "similarity_search": True,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        print(f"[ERROR] 위험 보고서 생성 실패: {e}")
        
        return {
            "status": "error",
            "message": f"보고서 생성 중 오류가 발생했습니다: {str(e)}",
            "report": {
                "suspicious_user_id": request.user_id,
                "post_id": request.post_id,
                "evidence_sentences": [],
                "similar_patterns": [],
                "why_flagged": f"분석 중 오류 발생: {str(e)}",
                "suggested_action": "수동 검토 필요",
                "priority": "MEDIUM",
                "risk_score": 0.0,
                "high_risk_count": 0,
                "total_sentences": 0,
                "analysis_timestamp": datetime.now().isoformat(),
                "error": True
            },
            "metadata": {
                "analysis_method": "rag_pipeline",
                "llm_enabled": False,
                "similarity_search": False,
                "timestamp": datetime.now().isoformat()
            }
        }

