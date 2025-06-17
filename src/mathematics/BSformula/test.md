```python
from src.mathematics.BSformula.bs76 import BS76
from src.mathematics.BSformula.constants import CD_RATE
c=BS76(F=100,K=100,T=1, price=3.2, r=0.03, option="Call")
p=BS76(F=100,K=100,T=1, price=5, r=0.03, option="Put")
print(f"콜옵션 내재 변동성 {c.impvol} 베가{c.vega()} 재계산한 옵션 가격 : {c.BS(100,100,1, c.impvol, CD_RATE)} ")
print(f"풋옵션 내재 변동성 {p.impvol} 베가{c.vega()} 재계산한 옵션 가격 : {p.BS(100,100,1, p.impvol, CD_RATE)} ")


```

- todo
  - CD금리 조회해서 적용
    - t3521 InBlock{"kind":"S","symbol":"KIR@CD91"}   OutBlock{"close"}
  - market variable class와  옵션 instrument 클래스를 구별 
  - 만기, 평가일을 입력받는 경우
  - 날짜 분단위까지 인식 yyyymmdd hh:mm
  - option series 관리
  - 최적화,  vectorization? 
  - 민감도 formaula vs finite difference비교 in speed and accuracy
  - 