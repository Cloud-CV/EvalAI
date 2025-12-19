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
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';
import { MatTableModule } from '@angular/material';
import { FormsModule } from '@angular/forms';

describe('ChallengeComponent', () => {
  let component: ChallengeComponent;
  let fixture: ComponentFixture<ChallengeComponent>;
  let authService, authServiceSpy;
  const fakeActivatedRoute = {
    id: 1,
  };
  let challengeService, challengeServiceSpy;
  let globalService, apiService, endpointsService;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [
        ChallengeComponent,
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
        SelectphaseComponent,
      ],
      providers: [
        ApiService,
        GlobalService,
        ChallengeService,
        AuthService,
        EndpointsService,
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {},
            params: of(fakeActivatedRoute),
          },
        },
      ],
      imports: [HttpClientModule, RouterTestingModule, FormsModule, MatTableModule],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChallengeComponent);
    challengeService = TestBed.get(ChallengeService);
    globalService = TestBed.get(GlobalService);
    authService = TestBed.get(AuthService);
    apiService = TestBed.get(ApiService);
    endpointsService = TestBed.get(EndpointsService);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('Global variables', () => {
    expect(component.isStarred).toBeFalsy();
    expect(component.isChallengeHost).toBeFalsy();
    expect(component.isParticipated).toBeFalsy();
    expect(component.isLoggedIn).toBeFalsy();
  });

  it('check if user is logged in', () => {
    authServiceSpy = spyOn(authService, 'isLoggedIn').and.returnValue(true);
    fixture.detectChanges();
    expect(authServiceSpy).toHaveBeenCalled();
    expect(component.isLoggedIn).toBeTruthy();
  });

  it('check activated routed subscribe method called on init', async(() => {
    challengeServiceSpy = spyOn(challengeService, 'fetchChallenge');
    fixture.detectChanges();
    expect(component.id).toBe(fakeActivatedRoute['id']);
    expect(challengeServiceSpy).toHaveBeenCalledWith(fakeActivatedRoute['id']);
  }));

  it('should call `starToggle` method when user is logged in', () => {
    challengeServiceSpy = spyOn(challengeService, 'starToggle');
    const challengeId = 1;
    component.isLoggedIn = true;
    component.starToggle(challengeId);
    expect(challengeServiceSpy).toHaveBeenCalledWith(challengeId);
  });

  it('should show login to star the challenge message when user is not logged in', () => {
    const challengeId = 1;
    component.isLoggedIn = false;
    component.starToggle(challengeId);
    expect(globalService.showToast).toHaveBeenCalledWith('error', 'Please login to star the challenge!', 5);
  });
});
