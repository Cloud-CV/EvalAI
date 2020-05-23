import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// import component
import { ChallengeComponent } from './challenge.component';
import { ChallengeoverviewComponent } from './challengeoverview/challengeoverview.component';
import { ChallengeevaluationComponent } from './challengeevaluation/challengeevaluation.component';
import { ChallengephasesComponent } from './challengephases/challengephases.component';
import { ChallengeparticipateComponent } from './challengeparticipate/challengeparticipate.component';
import { ChallengesubmitComponent } from './challengesubmit/challengesubmit.component';
import { ChallengesubmissionsComponent } from './challengesubmissions/challengesubmissions.component';
import { ChallengeviewallsubmissionsComponent } from './challengeviewallsubmissions/challengeviewallsubmissions.component';
import { ChallengeleaderboardComponent } from './challengeleaderboard/challengeleaderboard.component';
import { ChallengesettingsComponent } from './challengesettings/challengesettings.component';

const routes: Routes = [
  {
    path: '',
    component: ChallengeComponent,
    children: [
      {path: '', redirectTo: 'overview', pathMatch: 'full'},
      {path: 'overview', component: ChallengeoverviewComponent},
      {path: 'evaluation', component: ChallengeevaluationComponent},
      {path: 'phases', component: ChallengephasesComponent},
      {path: 'participate', component: ChallengeparticipateComponent},
      {path: 'submit', component: ChallengesubmitComponent},
      {path: 'my-submissions', component: ChallengesubmissionsComponent},
      {path: 'my-submissions/:phase', component: ChallengesubmissionsComponent},
      {path: 'mysubmissions/:phase/:submission', component: ChallengesubmissionsComponent},
      {path: 'view-all-submissions', component: ChallengeviewallsubmissionsComponent},
      {path: 'leaderboard', component: ChallengeleaderboardComponent},
      {path: 'leaderboard/:split', component: ChallengeleaderboardComponent},
      {path: 'leaderboard/:split/:entry', component: ChallengeleaderboardComponent},
      {path: 'settings', component: ChallengesettingsComponent}
    ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ChallengeRoutingModule { }
