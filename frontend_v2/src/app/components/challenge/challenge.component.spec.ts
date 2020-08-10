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
import { Router, ActivatedRoute } from '@angular/router';
import { Observable, of } from 'rxjs';
import { MatTableModule } from '@angular/material';
import { FormsModule } from '@angular/forms';

describe('ChallengeComponent', () => {
  let component: ChallengeComponent;
  let fixture: ComponentFixture<ChallengeComponent>;
  let router, authService, authServiceSpy;
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
    router = TestBed.get(Router);
    challengeService = TestBed.get(ChallengeService);
    globalService = TestBed.get(GlobalService);
    authService = TestBed.get(AuthService);
    apiService = TestBed.get(ApiService);
    endpointsService = TestBed.get(EndpointsService);
    component = fixture.componentInstance;

    spyOn(router, 'navigate');
    spyOn(globalService, 'handleApiError');
    spyOn(globalService, 'showToast');
    spyOn(globalService, 'showModal');
    spyOn(globalService, 'showConfirm');
    spyOn(endpointsService, 'editChallengeDetailsURL');
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('Global variables', () => {
    expect(component.isStarred).toBeFalsy();
    expect(component.isChallengeHost).toBeFalsy();
    expect(component.publishChallenge).toEqual({
      state: 'Not Published',
      icon: 'fa fa-eye-slash red-text',
    });
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

  it('should toggle the publish challenge state from public to private', async(() => {
    component.publishChallenge = {
      state: 'Published',
      icon: 'fa fa-eye green-text',
    };
    const expectedSuccessMsg = 'The challenge was successfully made private';
    spyOn(apiService, 'patchUrl').and.returnValue(
      new Observable((observer) => {
        observer.next({ results: [{}] });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.togglePublishChallengeState();
    fixture.detectChanges();
    expect(globalService.showConfirm).toHaveBeenCalled();
    component.apiCall();
    expect(apiService.patchUrl).toHaveBeenCalled();
    expect(component.publishChallenge.state).toEqual('Not Published');
    expect(component.publishChallenge.icon).toEqual('fa fa-eye-slash red-text');
    expect(globalService.showToast).toHaveBeenCalledWith('success', expectedSuccessMsg, 5);
  }));

  it('should toggle the publish challenge state from private to public', async(() => {
    component.publishChallenge = {
      state: 'Not Published',
      icon: 'fa fa-eye-slash red-text',
    };
    const expectedSuccessMsg = 'The challenge was successfully made public';
    spyOn(apiService, 'patchUrl').and.returnValue(
      new Observable((observer) => {
        observer.next({ results: [{}] });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.togglePublishChallengeState();
    fixture.detectChanges();
    expect(globalService.showConfirm).toHaveBeenCalled();
    component.apiCall();
    expect(apiService.patchUrl).toHaveBeenCalled();
    expect(component.publishChallenge.state).toEqual('Published');
    expect(component.publishChallenge.icon).toEqual('fa fa-eye green-text');
    expect(globalService.showToast).toHaveBeenCalledWith('success', expectedSuccessMsg, 5);
  }));

  it('should handle the API error for `togglePublishChallengeState` method', async(() => {
    const expectedApiError = {
      error: 'Api error',
    };
    spyOn(apiService, 'patchUrl').and.returnValue(
      new Observable((observer) => {
        observer.error({ error: expectedApiError.error });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.togglePublishChallengeState();
    fixture.detectChanges();
    expect(globalService.showConfirm).toHaveBeenCalled();
    component.apiCall();
    expect(apiService.patchUrl).toHaveBeenCalled();
    expect(globalService.handleApiError).toHaveBeenCalledWith(expectedApiError, true);
    expect(globalService.showToast).toHaveBeenCalledWith('error', expectedApiError);
  }));

  it('should show the modal and successfully edit the title of a challenge', async(() => {
    component.challenge = {
      id: 1,
      title: 'Challenge title',
      creator: 'Host user',
      description: 'Challenge description',
    };
    const expectedUpdateTitle = 'Updated challenge title';
    const expectedSuccessMsg = 'The challenge title is  successfully updated!';
    spyOn(apiService, 'patchUrl').and.returnValue(
      new Observable((observer) => {
        observer.next({ title: expectedUpdateTitle });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.editChallengeTitle();
    fixture.detectChanges();
    expect(globalService.showModal).toHaveBeenCalled();
    component.apiCall();
    expect(apiService.patchUrl).toHaveBeenCalled();
    expect(component.challenge.title).toEqual(expectedUpdateTitle);
    expect(globalService.showToast).toHaveBeenCalledWith('success', expectedSuccessMsg, 5);
  }));

  it('should handle the API error for `editChallengeTitle` method', async(() => {
    component.challenge = {
      id: 1,
      title: 'Challenge title',
      creator: 'Host user',
      description: 'Challenge description',
    };
    const expectedApiError = {
      error: 'Api error',
    };
    spyOn(apiService, 'patchUrl').and.returnValue(
      new Observable((observer) => {
        observer.error({ error: expectedApiError.error });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.editChallengeTitle();
    fixture.detectChanges();
    expect(globalService.showModal).toHaveBeenCalled();
    component.apiCall();
    expect(apiService.patchUrl).toHaveBeenCalled();
    expect(globalService.handleApiError).toHaveBeenCalledWith(expectedApiError, true);
    expect(globalService.showToast).toHaveBeenCalledWith('error', expectedApiError);
  }));

  it('should show the modal with the form fields and successfully delete the challenge', async(() => {
    const expectedSuccessMsg = 'The Challenge is successfully deleted!';
    spyOn(apiService, 'postUrl').and.returnValue(
      new Observable((observer) => {
        observer.next({ results: [{}] });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.deleteChallenge();
    fixture.detectChanges();
    expect(globalService.showModal).toHaveBeenCalled();
    component.apiCall();
    expect(apiService.postUrl).toHaveBeenCalled();
    expect(router.navigate).toHaveBeenCalledWith(['/challenges/all']);
    expect(globalService.showToast).toHaveBeenCalledWith('success', expectedSuccessMsg, 5);
  }));

  it('should handle the API error for `deleteChallenge` method', async(() => {
    const expectedApiError = {
      error: 'Api error',
    };
    spyOn(apiService, 'postUrl').and.returnValue(
      new Observable((observer) => {
        observer.error({ error: expectedApiError.error });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.deleteChallenge();
    fixture.detectChanges();
    expect(globalService.showModal).toHaveBeenCalled();
    component.apiCall();
    expect(apiService.postUrl).toHaveBeenCalled();
    expect(globalService.handleApiError).toHaveBeenCalledWith(expectedApiError, true);
    expect(globalService.showToast).toHaveBeenCalledWith('error', expectedApiError);
  }));
});
