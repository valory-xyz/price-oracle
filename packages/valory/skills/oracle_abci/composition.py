# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This module contains the price estimation ABCI application."""

from packages.valory.skills.abstract_round_abci.abci_app_chain import (
    AbciAppTransitionMapping,
    chain,
)
from packages.valory.skills.abstract_round_abci.base import get_name
from packages.valory.skills.oracle_deployment_abci.rounds import (
    FinishedOracleRound,
    OracleDeploymentAbciApp,
    SetupCheckRound,
)
from packages.valory.skills.oracle_deployment_abci.rounds import (
    SynchronizedData as ODSynchronizedData,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    CollectObservationRound,
    FinishedPriceAggregationRound,
    PriceAggregationAbciApp,
)
from packages.valory.skills.registration_abci.rounds import (
    AgentRegistrationAbciApp,
    FinishedRegistrationFFWRound,
    FinishedRegistrationRound,
    RegistrationRound,
)
from packages.valory.skills.reset_pause_abci.rounds import (
    FinishedResetAndPauseErrorRound,
    FinishedResetAndPauseRound,
    ResetAndPauseRound,
    ResetPauseAbciApp,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    FailedRound,
    FinishedTransactionSubmissionRound,
    RandomnessTransactionSubmissionRound,
    TransactionSubmissionAbciApp,
)


abci_app_transition_mapping: AbciAppTransitionMapping = {
    FinishedRegistrationRound: SetupCheckRound,
    FinishedRegistrationFFWRound: SetupCheckRound,
    FinishedOracleRound: CollectObservationRound,
    FinishedPriceAggregationRound: RandomnessTransactionSubmissionRound,
    FailedRound: ResetAndPauseRound,
    FinishedTransactionSubmissionRound: ResetAndPauseRound,
    FinishedResetAndPauseRound: CollectObservationRound,
    FinishedResetAndPauseErrorRound: RegistrationRound,
}

AgentRegistrationAbciApp.db_post_conditions[FinishedRegistrationFFWRound].extend(
    [
        get_name(ODSynchronizedData.oracle_contract_address),
        # this is a patch and needs to be addressed in the autonomy repo
        # we need to add this in the post-conditions of the registration abci
        "safe_contract_address",
    ]
)

AgentRegistrationAbciApp.db_post_conditions[FinishedRegistrationRound].extend(
    [
        # this is a patch and needs to be addressed in the autonomy repo
        # we need to add this in the post-conditions of the registration abci
        "safe_contract_address",
    ]
)

OracleAbciApp = chain(
    (
        AgentRegistrationAbciApp,
        OracleDeploymentAbciApp,
        PriceAggregationAbciApp,
        TransactionSubmissionAbciApp,
        ResetPauseAbciApp,
    ),
    abci_app_transition_mapping,
)
