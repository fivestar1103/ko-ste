from calibration.scripts.mine_pairs import (
    align_block, classify, join_list_continuations, md_sentences, rst_sentences,
)


def test_identical_text_with_different_sentence_breaks_is_reflow():
    assert classify(["가는 나를 본다."], ["가는", "나를 본다."]) == "reflow"


def test_code_or_number_change_is_not_a_style_edit():
    assert classify(["`a`를 3번 실행한다."], ["`b`를 3번 실행한다."]) == "token"
    assert classify(["3번 실행한다."], ["4번 실행한다."]) == "token"


def test_one_letter_fix_is_minor_and_rewording_is_rewrite():
    assert classify(["인증서 생성는 단계를 설명한다."], ["인증서 생성은 단계를 설명한다."]) == "minor"
    assert classify(["배포 수행이 필요하다."], ["배포가 필요하다."]) == "rewrite"


def test_split_sentence_is_aligned_as_one_pair():
    old = ["마운트 옵션의 유효성이 검사되지 않으므로 마운트 옵션이 유효하지 않으면 마운트가 실패한다."]
    new = ["마운트 옵션의 유효성이 검사되지 않는다.", "마운트 옵션이 유효하지 않으면, 마운트가 실패한다."]
    [(oi, nj, _)] = align_block(old, new)
    assert (oi, nj) == ([0], [0, 1])


def test_unrelated_sentences_are_not_paired():
    assert align_block(["캐시는 메모리를 쓴다."], ["로그는 하루 뒤 지워진다."]) == []


def test_list_item_continuation_stays_one_sentence():
    md = "- 리소스 타입은 대소문자를 구분하지 않으며\n  단수형을 지정할 수 있다.\n"
    assert md_sentences(join_list_continuations(md)) == ["리소스 타입은 대소문자를 구분하지 않으며 단수형을 지정할 수 있다."]


def test_hugo_shortcodes_keep_tooltip_text_and_drop_wrappers():
    md = '{{< note >}} {{< glossary_tooltip text="파드" term_id="pod" >}}는 노드에서 실행된다. {{< /note >}}\n'
    assert md_sentences(md) == ["파드는 노드에서 실행된다."]


def test_rst_drops_titles_directives_and_literal_blocks():
    rst = "제목\n====\n\n다음 명령을 실행합니다::\n\n    pip install torch\n\n.. note::\n   메모입니다.\n\n설치가 끝나면 모델을 불러옵니다.\n"
    assert rst_sentences(rst) == ["다음 명령을 실행합니다:", "설치가 끝나면 모델을 불러옵니다."]
