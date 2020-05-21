import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  MatChipsModule,
  MatTableModule,
  MatMenuModule,
  MatSelectModule,
  MatIconModule,
  MatDividerModule,
  MatCheckboxModule } from '@angular/material';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { FroalaEditorModule, FroalaViewModule } from 'angular-froala-wysiwyg';

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
import { TermsAndConditionsModalComponent } from './challengeparticipate/terms-and-conditions-modal/terms-and-conditions-modal.component';
import { EditphasemodalComponent } from './challengephases/editphasemodal/editphasemodal.component';
import { PhasecardComponent } from './challengephases/phasecard/phasecard.component';
import { ChallengeComponent } from './challenge.component';

// import Modules
import { NavModule } from '../nav/nav.module';
import { ChallengeRoutingModule } from './challenge-routing.module';
import { PubliclistModule } from '../publiclists/publiclist.module';

// import services
import { ApiService } from '../../services/api.service';
import { ChallengeService } from '../../services/challenge.service';
import { AuthService } from '../../services/auth.service';
import { GlobalService } from '../../services/global.service';

@NgModule({
  declarations: [
    ChallengeevaluationComponent,
    ChallengeleaderboardComponent,
    ChallengeoverviewComponent,
    ChallengeparticipateComponent,
    ChallengephasesComponent,
    EditphasemodalComponent,
    PhasecardComponent,
    ChallengesettingsComponent,
    ChallengesubmissionsComponent,
    ChallengesubmitComponent,
    ChallengeviewallsubmissionsComponent,
    TermsAndConditionsModalComponent,
    ChallengeComponent
  ],
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    MatChipsModule,
    MatTableModule,
    MatMenuModule,
    MatSelectModule,
    MatIconModule,
    MatDividerModule,
    MatCheckboxModule,
    FroalaEditorModule.forRoot(),
    FroalaViewModule.forRoot(),
    ChallengeRoutingModule,
    PubliclistModule,
    NavModule
  ],
  exports: [
    ChallengeevaluationComponent,
    ChallengeleaderboardComponent,
    ChallengeoverviewComponent,
    ChallengeparticipateComponent,
    ChallengephasesComponent,
    EditphasemodalComponent,
    PhasecardComponent,
    ChallengesettingsComponent,
    ChallengesubmissionsComponent,
    ChallengesubmitComponent,
    ChallengeviewallsubmissionsComponent,
    TermsAndConditionsModalComponent,
    ChallengeComponent,
    PubliclistModule,
    NavModule
  ],
  providers: [
    ChallengeService,
    ApiService,
    AuthService,
    GlobalService
  ],
  schemas: [ CUSTOM_ELEMENTS_SCHEMA ],
})
export class ChallengeModule { }
