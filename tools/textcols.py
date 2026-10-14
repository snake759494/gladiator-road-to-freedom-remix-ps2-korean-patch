import re
# (파일 정규식, 열 이름 집합 or None=모든 열)
RULES=[
 (r'SERIFU_.*', {'セリフ１','セリフ２'}),
 (r'(KUN_S_.*_J|HK_MAGE_J|ISYA_J|KEIBIHEI_J|KOUGYOU_MAGE_J|SERIFU_(DEKI|GUNA|KERA|KUSA|MAGE|RALU|ZAKO))', {'セリフ１','セリフ２'}),
 (r'MENU_J', {'文字'}),
 (r'ENDING\d*', {'文字１','文字２'}),
 (r'DEMO_J', {'0','1','2','3','4','5','6','7'}),
 (r'PANEL_A_.*_J', {'パネル名','コメント1','コメント2','コメント3','コメント4','コメント5','コメント6'}),
 (r'PANEL_PASSIVE_J', {'パネル名','コメント'}),
 (r'P_A_MANAGE', {'日本語'}),
 (r'KGMENU_OPTIONS', {'邦文'}),
 (r'CTRL_GUIDANCE', {'邦文１','邦文２','邦文３','邦文４'}),
 (r'TRA_COMMENT', None),
 (r'KEIKOKU', {'日本語メッセージ１','日本語メッセージ２'}),
 (r'MC_KEIKOKU_J', {'警告'}),
 (r'K_SAKUSEI_J', {'出身','前職業','神','生き様'}),
 (r'KUNREN_(INFO|MENU)', {'テキスト'}),
 (r'TRAINING', {'メニュー日本語'}),
 (r'DUEL_ENT', {'speech'}),
 (r'KG_INTRO', {'セリフ1-1','セリフ1-2','セリフ2-1','セリフ2-2'}),
 (r'REP_TABLE', None),
 (r'OPTION_KANRI_J', {'データ１'}),
 (r'VOICE', {'日本語訳'}),
 (r'SOUND_TEST', {'日本語','内容'}),
]
def cols_for(fname):
    n=fname.replace('DATA/','').replace('.CSB','')
    if n.endswith('_E'): return set()
    for pat,cols in RULES:
        if re.fullmatch(pat,n): return cols if cols is not None else 'ALL'
    return set()

# ARY(컴파일 테이블) 중 표시용 문자열을 바꿀 파일
ARY_OK={'CTRL_GUIDANCE','ENDING','ENDING00','ENDING01','ENDING02','ENDING03','ENDING04','ENDING05','ENDING06',
 'KEIKOKU','KGMENU_OPTIONS','KG_INTRO','K_SAKUSEI_J','S_SAKUSEI_J','MC_KEIKOKU_J','MENU_J',
 'PANEL_A_LARGE_SHIELD_J','PANEL_A_ONE_SWORD_J','PANEL_A_STRIKER_J','PANEL_A_TWO_SWORDS_J','PANEL_PASSIVE_J',
 'REP_TABLE','TRA_COMMENT'}
KEEP={'ロゴ','ランダム','プレーヤー名','終わり'}   # 연출·스크립트 지시어(엔딩 로고, 메뉴의 무작위 이름·이름 출력·종료)

# 일본어 모드에서도 영어로 표시되는 값 (work/en_ko.tsv 로 번역)
EN_CSB={'OBJ_FRG':{'名前'},'SALVO_TABLE':{'Title'},'PANEL_PASSIVE_J':{'パネル名'},'PANEL_A_LEVEL_J':{'パネル名'},
 'KUNREN_INFO':{'テキスト'},'OPTION_KANRI_J':{'データ１'},'KGMENU_LAYOUT':{'カーソル用'}}
EN_ARY={'OBJ','OBJ_FRG','SALVO_TABLE','PANEL_PASSIVE_J','PANEL_A_LEVEL_J','KUNREN_INFO','KGMENU_LAYOUT'}
def load_en():
    d={}
    for l in open('D:/ps2/글라디에이터_로드투프리덤_리믹스/work/en_ko.tsv',encoding='utf8'):
        l=l.rstrip(chr(10))
        if chr(9) in l:
            a,b=l.split(chr(9),1)
            if a!=b: d[a]=b
    return d
