from app.sar.failure_recovery import A17RecoveryHarness, ExecutionState, InjectedTransport, TimeoutClass


def test_pre_dispatch_is_only_direct_retryable_timeout():
    h = A17RecoveryHarness()
    decision = h.classify(TimeoutClass.PRE_DISPATCH)
    assert decision.retry is True
    assert decision.verify_effect is False
    assert decision.state == ExecutionState.NOT_DISPATCHED


def test_acknowledged_and_post_effect_require_verification():
    h = A17RecoveryHarness()
    for timeout_class in (TimeoutClass.ACKNOWLEDGED, TimeoutClass.POST_EFFECT_RESPONSE_LOSS):
        decision = h.classify(timeout_class)
        assert decision.retry is False
        assert decision.verify_effect is True
        assert decision.state == ExecutionState.EXECUTION_UNKNOWN


def test_dependency_timeout_escalates_without_retry():
    decision = A17RecoveryHarness().classify(TimeoutClass.DEPENDENCY)
    assert decision.retry is False
    assert decision.escalate_h1 is True


def test_effect_confirmed_never_retries():
    decision = A17RecoveryHarness().recover_unknown(lambda: True, retry_count=0)
    assert decision.state == ExecutionState.EFFECT_CONFIRMED
    assert decision.retry is False


def test_no_effect_allows_only_bounded_retry():
    h = A17RecoveryHarness()
    first = h.recover_unknown(lambda: False, retry_count=0, max_retries=1)
    assert first.retry is True
    exhausted = h.recover_unknown(lambda: False, retry_count=1, max_retries=1)
    assert exhausted.retry is False
    assert exhausted.escalate_h1 is True


def test_inconclusive_verification_escalates_h1():
    decision = A17RecoveryHarness().recover_unknown(lambda: None, retry_count=0)
    assert decision.state == ExecutionState.H1_ESCALATION
    assert decision.escalate_h1 is True


def test_fault_injector_distinguishes_no_effect_and_post_effect_loss():
    effects = []
    pre = InjectedTransport(TimeoutClass.PRE_DISPATCH)
    try:
        pre.dispatch(lambda: effects.append("x"))
    except TimeoutError:
        pass
    assert pre.received is False and effects == []

    post = InjectedTransport(TimeoutClass.POST_EFFECT_RESPONSE_LOSS)
    try:
        post.dispatch(lambda: effects.append("x"))
    except TimeoutError:
        pass
    assert post.received is True
    assert post.effect_applied is True
    assert effects == ["x"]
