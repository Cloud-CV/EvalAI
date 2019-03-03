import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { HeaderStaticComponent } from '../../components/nav/header-static/header-static.component';
import { ChallengeComponent } from './challenge.component';
import { ApiService } from '../../services/api.service';
import { GlobalService } from '../../services/global.service';
import { ChallengeService } from '../../services/challenge.service';
import { HttpClientModule } from '@angular/common/http';
import { ChallengeoverviewComponent } from '../../components/challenge/challengeoverview/challengeoverview.component';
import { ChallengeevaluationComponent } from '../../components/challenge/challengeevaluation/challengeevaluation.component';
import { ChallengephasesComponent } from '../../components/challenge/challengephases/challengephases.component';
import { ChallengeparticipateComponent } from '../../components/challenge/challengeparticipate/challengeparticipate.component';
import { ChallengeleaderboardComponent } from '../../components/challenge/challengeleaderboard/challengeleaderboard.component';
import { ChallengesubmitComponent } from '../../components/challenge/challengesubmit/challengesubmit.component';
import { ChallengesubmissionsComponent } from '../../components/challenge/challengesubmissions/challengesubmissions.component';
import { PhasecardComponent } from '../../components/challenge/challengephases/phasecard/phasecard.component';
import { RouterTestingModule } from '@angular/router/testing';
import { AuthService } from '../../services/auth.service';
import { EndpointsService } from '../../services/endpoints.service';
import { ForceloginComponent } from '../../components/utility/forcelogin/forcelogin.component';
import { FooterComponent } from '../../components/nav/footer/footer.component';
import { TeamlistComponent } from '../../components/publiclists/teamlist/teamlist.component';
import { SelectphaseComponent } from '../../components/utility/selectphase/selectphase.component';
import { InputComponent } from '../../components/utility/input/input.component';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('ChallengeComponent', () => {
  let component: ChallengeComponent;
  let fixture: ComponentFixture<ChallengeComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ChallengeComponent,
                      HeaderStaticComponent,
                      ChallengeoverviewComponent,
                      ChallengeevaluationComponent,
                      ChallengephasesComponent,
                      ChallengeparticipateComponent,
                      ChallengeleaderboardComponent,
                      ChallengesubmitComponent,
                      ChallengesubmissionsComponent,
                      PhasecardComponent,
                      ForceloginComponent,
                      FooterComponent,
                      TeamlistComponent,
                      SelectphaseComponent ],
      providers: [ ApiService, GlobalService, ChallengeService, AuthService, EndpointsService ],
      imports: [ HttpClientModule, RouterTestingModule ],
      schemas: [ NO_ERRORS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChallengeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
