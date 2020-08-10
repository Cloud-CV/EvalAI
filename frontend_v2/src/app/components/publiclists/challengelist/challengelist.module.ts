import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatTabsModule } from '@angular/material';

// import component
import { ChallengecardComponent } from './challengecard/challengecard.component';
import { ChallengelistComponent } from './challengelist.component';
import { TeamlistComponent } from '../teamlist/teamlist.component';
import { TeamcardComponent } from '../teamlist/teamcard/teamcard.component';
import { CardlistComponent } from '../../utility/cardlist/cardlist.component';

// import module
import { SharedModule } from '../../../shared/shared.module';
import { AnalyticsModule } from '../../analytics/analytics.module';

@NgModule({
  declarations: [
    ChallengelistComponent,
    ChallengecardComponent,
    TeamcardComponent,
    TeamlistComponent,
    CardlistComponent,
  ],
  imports: [CommonModule, RouterModule, MatTabsModule, SharedModule, AnalyticsModule],
  exports: [ChallengelistComponent, ChallengecardComponent, TeamcardComponent, TeamlistComponent, CardlistComponent],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
})
export class ChallengelistModule {}
