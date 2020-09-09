import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  MatChipsModule,
  MatTableModule,
  MatMenuModule,
  MatSelectModule,
  MatIconModule,
  MatDividerModule,
  MatCheckboxModule,
  MatRadioModule,
  MatDialogModule,
  MatSliderModule,
} from '@angular/material';

// import components
import { ChallengeevaluationComponent } from './challengeevaluation/challengeevaluation.component';
import { ChallengeleaderboardComponent } from './challengeleaderboard/challengeleaderboard.component';
import { ChallengeoverviewComponent } from './challengeoverview/challengeoverview.component';
import { ChallengeparticipateComponent } from './challengeparticipate/challengeparticipate.component';
import { ChallengephasesComponent } from './challengephases/challengephases.component';
import { ChallengesettingsComponent } from './challengesettings/challengesettings.component';
import { ChallengesubmissionsComponent } from './challengesubmissions/challengesubmissions.component';
import { ChallengesubmitComponent } from './challengesubmit/challengesubmit.component';
import { ChallengeviewallsubmissionsComponent } from './challengeviewallsubmissions/challengeviewallsubmissions.component';
import { PhasecardComponent } from './challengephases/phasecard/phasecard.component';
import { ChallengeComponent } from './challenge.component';

// import module
import { ChallengeRoutingModule } from './challenge-routing.module';
import { SharedModule } from '../../shared/shared.module';
import { ChallengelistModule } from '../publiclists/challengelist/challengelist.module';
import { SubmissionMetaAttributesDialogueComponent } from './submission-meta-attributes-dialogue/submission-meta-attributes-dialogue.component';
import { ChallengediscussComponent } from './challengediscuss/challengediscuss.component';
import { ChallengeanalyticsComponent } from './challengeanalytics/challengeanalytics.component';

@NgModule({
  declarations: [
    ChallengeComponent,
    ChallengesettingsComponent,
    ChallengeoverviewComponent,
    ChallengeevaluationComponent,
    ChallengephasesComponent,
    ChallengeparticipateComponent,
    ChallengeleaderboardComponent,
    ChallengesubmitComponent,
    ChallengesubmissionsComponent,
    ChallengeviewallsubmissionsComponent,
    PhasecardComponent,
    SubmissionMetaAttributesDialogueComponent,
    ChallengediscussComponent,
    ChallengeanalyticsComponent,
  ],
  imports: [
    CommonModule,
    ChallengeRoutingModule,
    SharedModule,
    MatChipsModule,
    MatIconModule,
    ChallengelistModule,
    MatSelectModule,
    MatTableModule,
    MatCheckboxModule,
    MatDividerModule,
    MatMenuModule,
    MatRadioModule,
    MatDialogModule,
    MatSliderModule,
  ],
  exports: [
    ChallengeComponent,
    ChallengesettingsComponent,
    ChallengeoverviewComponent,
    ChallengeevaluationComponent,
    ChallengephasesComponent,
    ChallengeparticipateComponent,
    ChallengeleaderboardComponent,
    ChallengesubmitComponent,
    ChallengesubmissionsComponent,
    ChallengeviewallsubmissionsComponent,
    PhasecardComponent,
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
  entryComponents: [SubmissionMetaAttributesDialogueComponent],
})
export class ChallengeModule {}
