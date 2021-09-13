import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ChallengesettingsComponent } from './challengesettings.component';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { GlobalService } from '../../../services/global.service';
import { ChallengeService } from '../../../services/challenge.service';
import { ApiService } from '../../../services/api.service';
import { WindowService } from '../../../services/window.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { HttpClientModule } from '@angular/common/http';
import { RouterTestingModule } from '@angular/router/testing';
import { Observable } from 'rxjs';
import { Router } from '@angular/router';

describe('ChallengesettingsComponent', () => {
  let component: ChallengesettingsComponent;
  let fixture: ComponentFixture<ChallengesettingsComponent>;

  let globalService, apiService, endpointsService, router;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ChallengesettingsComponent],
      providers: [ChallengeService, GlobalService, ApiService, WindowService, EndpointsService],
      imports: [RouterTestingModule, HttpClientModule],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChallengesettingsComponent);
    router = TestBed.get(Router);
    globalService = TestBed.get(GlobalService);
    apiService = TestBed.get(ApiService);
    component = fixture.componentInstance;

    spyOn(router, 'navigate');
    spyOn(globalService, 'handleApiError');
    spyOn(globalService, 'showToast');
    spyOn(globalService, 'showModal');
    spyOn(globalService, 'showConfirm');
    spyOn(endpointsService, 'editChallengeDetailsURL');

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('Global variables', () => {
    expect(component.isChallengeHost).toBeFalsy();
    expect(component.publishChallenge).toEqual({
      state: 'Not Published',
      icon: 'fa fa-eye-slash red-text',
    });
    expect(component.phaseVisibility).toEqual({
      state: 'Private',
      icon: 'fa fa-toggle-off grey-text text-darken-1',
    });
    expect(component.submissionVisibility).toEqual({
      state: 'Private',
      icon: 'fa fa-toggle-off grey-text text-darken-1',
    });
    expect(component.leaderboardVisibility).toEqual({
      state: 'Private',
      icon: 'fa fa-toggle-off grey-text text-darken-1',
    });
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
        spyOn(globalService, 'showModal');
        spyOn(globalService, 'showToast');
        spyOn(component, 'updateView');
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

  it('should show modal and successfully edit the evaluation details', () => {
    const updatedEvaluationDetails = 'Updated challenge evaluation details';
    const expectedSuccessMsg = 'The evaluation details is successfully updated!';
    spyOn(apiService, 'patchUrl').and.returnValue(
      new Observable((observer) => {
        observer.next({ evaluation_details: updatedEvaluationDetails });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.editEvaluationCriteria();
    expect(globalService.showModal).toHaveBeenCalled();
    component.apiCall(updatedEvaluationDetails);
    expect(apiService.patchUrl).toHaveBeenCalled();
    expect(component.challenge.evaluation_details).toEqual(updatedEvaluationDetails);
    expect(component.updateView).toHaveBeenCalled();
    expect(component.challenge.evaluation_details).toEqual(updatedEvaluationDetails);
    expect(globalService.showToast).toHaveBeenCalledWith('success', expectedSuccessMsg, 5);
  });

  it('should handle the API error for `editEvaluationCriteria` method', () => {
    const updatedEvaluationDetails = 'Updated challenge evaluation details';
    const expectedErrorMsg = {
      error: 'Api error',
    };
    spyOn(apiService, 'patchUrl').and.returnValue(
      new Observable((observer) => {
        observer.error({ error: expectedErrorMsg.error });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.editEvaluationCriteria();
    expect(globalService.showModal).toHaveBeenCalled();
    component.apiCall(updatedEvaluationDetails);
    expect(apiService.patchUrl).toHaveBeenCalled();
    expect(globalService.showToast).toHaveBeenCalledWith('error', expectedErrorMsg);
  });

  it('should show modal and successfully edit the terms and conditions', () => {
    const updatedTermsAndConditions = 'Updated terms and conditions of challenge';
    const expectedSuccessMsg = 'The terms and conditions are successfully updated!';
    spyOn(apiService, 'patchUrl').and.returnValue(
      new Observable((observer) => {
        observer.next({ terms_and_conditions: updatedTermsAndConditions });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.editTermsAndConditions();
    expect(globalService.showModal).toHaveBeenCalled();
    component.apiCall(updatedTermsAndConditions);
    expect(apiService.patchUrl).toHaveBeenCalled();
    expect(component.challenge.terms_and_conditions).toEqual(updatedTermsAndConditions);
    expect(component.updateView).toHaveBeenCalled();
    expect(component.challenge.terms_and_conditions).toEqual(updatedTermsAndConditions);
    expect(globalService.showToast).toHaveBeenCalledWith('success', expectedSuccessMsg, 5);
  });

  it('should handle the API error for `editTermsAndConditions` method', () => {
    const updatedTermsAndConditions = 'Updated terms and conditions of challenge';
    const expectedErrorMsg = {
      error: 'Api error',
    };
    spyOn(apiService, 'patchUrl').and.returnValue(
      new Observable((observer) => {
        observer.error({ error: expectedErrorMsg.error });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.editTermsAndConditions();
    expect(globalService.showModal).toHaveBeenCalled();
    component.apiCall(updatedTermsAndConditions);
    expect(apiService.patchUrl).toHaveBeenCalled();
    expect(globalService.showToast).toHaveBeenCalledWith('error', expectedErrorMsg);
  });

  it('should show modal and successfully update evaluation script', () => {
    const parameters = {
      evaluation_script: 'evaluation_script',
    };
    const expectedSuccessMsg = 'The evaluation script is successfully updated!';
    spyOn(apiService, 'patchFileUrl').and.returnValue(
      new Observable((observer) => {
        observer.next({ results: [{}] });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.editEvaluationScript();
    expect(globalService.showModal).toHaveBeenCalled();
    component.apiCall(parameters);
    expect(apiService.patchFileUrl).toHaveBeenCalled();
    expect(globalService.showToast).toHaveBeenCalledWith('success', expectedSuccessMsg);
  });

  it('should handle the API error for `editEvaluationScript` method', () => {
    const parameters = {
      evaluation_script: 'evaluation_script',
    };
    const expectedErrorMsg = {
      error: 'Api error',
    };
    spyOn(apiService, 'patchFileUrl').and.returnValue(
      new Observable((observer) => {
        observer.error({ error: expectedErrorMsg.error });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.editEvaluationScript();
    expect(globalService.showModal).toHaveBeenCalled();
    component.apiCall(parameters);
    expect(apiService.patchFileUrl).toHaveBeenCalled();
    expect(globalService.showToast).toHaveBeenCalledWith('error', expectedErrorMsg);
  });
  
  it('should show modal and successfully edit challenge description', () => {
    const updatedDescription = 'Updated challenge description';
    const expectedSuccessMsg = 'The description is successfully updated!';
    spyOn(apiService, 'patchUrl').and.returnValue(
      new Observable((observer) => {
        observer.next({ results: [{}] });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.editChallengeOverview();
    expect(globalService.showModal).toHaveBeenCalled();
    component.apiCall(updatedDescription);
    expect(apiService.patchUrl).toHaveBeenCalled();
    expect(globalService.showToast).toHaveBeenCalledWith('success', expectedSuccessMsg, 5);
  });

  it('should handle the API error for `editChallengeOverview` method', () => {
    const updatedDescription = 'Updated challenge description';
    const expectedErrorMsg = {
      error: 'Api error',
    };
    spyOn(apiService, 'patchUrl').and.returnValue(
      new Observable((observer) => {
        observer.error({ error: expectedErrorMsg.error });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.editChallengeOverview();
    expect(globalService.showModal).toHaveBeenCalled();
    component.apiCall(updatedDescription);
    expect(apiService.patchUrl).toHaveBeenCalled();
    expect(globalService.showToast).toHaveBeenCalledWith('error', expectedErrorMsg);
  });

  it('should toggle the phase visibility state from public to private', async(() => {
    component.phaseVisibility = {
      state: 'Public',
      icon: 'fa fa-toggle-on green-text',
    };
    const expectedSuccessMsg = 'The phase was successfully made private';
    spyOn(apiService, 'patchFileUrl').and.returnValue(
      new Observable((observer) => {
        observer.next({ results: [{}] });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.togglePhaseVisibility();
    fixture.detectChanges();
    expect(apiService.patchFileUrl).toHaveBeenCalled();
    expect(component.phaseVisibility.state).toEqual('Private');
    expect(component.phaseVisibility.icon).toEqual('fa fa-toggle-off grey-text text-darken-1');
    expect(globalService.showToast).toHaveBeenCalledWith('success', expectedSuccessMsg, 5);
  }));

  it('should toggle the phase visiblity state from private to public', async(() => {
    component.phaseVisibility = {
      state: 'Private',
      icon: 'fa fa-toggle-off grey-text text-darken-1',
    };
    const expectedSuccessMsg = 'The phase was successfully made public';
    spyOn(apiService, 'patchFileUrl').and.returnValue(
      new Observable((observer) => {
        observer.next({ results: [{}] });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.togglePhaseVisibility();
    fixture.detectChanges();
    expect(apiService.patchFIleUrl).toHaveBeenCalled();
    expect(component.phaseVisibility.state).toEqual('Public');
    expect(component.phaseVisibility.icon).toEqual('fa fa-toggle-on green-text');
    expect(globalService.showToast).toHaveBeenCalledWith('success', expectedSuccessMsg, 5);
  }));

  it('should handle the API error for `togglePhaseVisiblity` method', async(() => {
    const expectedApiError = {
      error: 'Api error',
    };
    spyOn(apiService, 'patchFileUrl').and.returnValue(
      new Observable((observer) => {
        observer.error({ error: expectedApiError.error });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.togglePhaseVisibility();
    fixture.detectChanges();
    expect(apiService.patchFileUrl).toHaveBeenCalled();
    expect(globalService.handleApiError).toHaveBeenCalledWith(expectedApiError, true);
    expect(globalService.showToast).toHaveBeenCalledWith('error', expectedApiError);
  }));

  it('should toggle the submission visibility state from public to private', async(() => {
    component.submissionVisibility = {
      state: 'Public',
      icon: 'fa fa-toggle-on green-text',
    };
    component.isLeaderboardPublic = true;
    const expectedSuccessMsg = 'The submissions were successfully made private';
    spyOn(apiService, 'patchFileUrl').and.returnValue(
      new Observable((observer) => {
        observer.next({ results: [{}] });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.toggleSubmissionVisibility();
    fixture.detectChanges();
    expect(apiService.patchFileUrl).toHaveBeenCalled();
    expect(component.submissionVisibility.state).toEqual('Private');
    expect(component.submissionVisibility.icon).toEqual('fa fa-toggle-off grey-text text-darken-1');
    expect(globalService.showToast).toHaveBeenCalledWith('success', expectedSuccessMsg, 5);
  }));

  it('should toggle the submission visibility state from private to public', async(() => {
    component.submissionVisibility = {
      state: 'Private',
      icon: 'fa fa-toggle-off grey-text text-darken-1',
    };
    component.isLeaderboardPublic = true;
    const expectedSuccessMsg = 'The submissions were successfully made public';
    spyOn(apiService, 'patchFileUrl').and.returnValue(
      new Observable((observer) => {
        observer.next({ results: [{}] });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.toggleSubmissionVisibility();
    fixture.detectChanges();
    expect(apiService.patchFileUrl).toHaveBeenCalled();
    expect(component.submissionVisibility.state).toEqual('Public');
    expect(component.submissionVisibility.icon).toEqual('fa fa-toggle-on green-text');
    expect(globalService.showToast).toHaveBeenCalledWith('success', expectedSuccessMsg, 5);
  }));

  it('should not toggle the submission visibility state when leaderboard_public is false', async(() => {
    component.submissionVisibility = {
      state: 'Public',
      icon: 'fa fa-toggle-on green-text',
    };
    component.isLeaderboardPublic = false;
    const expectedErrorMsg = 'Leaderboard is private, please make the leaderbaord public';

    component.toggleSubmissionVisibility();
    fixture.detectChanges();
    expect(component.submissionVisibility.state).toEqual('Public');
    expect(component.submissionVisibility.icon).toEqual('fa fa-toggle-on green-text');
    expect(globalService.showToast).toHaveBeenCalledWith('error', expectedErrorMsg, 5);
  }));

  it('should handle the API error for `toggleSubmissionVisiblity` method', async(() => {
    const expectedApiError = {
      error: 'Api error',
    };
    spyOn(apiService, 'patchFileUrl').and.returnValue(
      new Observable((observer) => {
        observer.error({ error: expectedApiError.error });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.toggleSubmissionVisibility();
    fixture.detectChanges();
    expect(apiService.patchUrl).toHaveBeenCalled();
    expect(globalService.handleApiError).toHaveBeenCalledWith(expectedApiError, true);
    expect(globalService.showToast).toHaveBeenCalledWith('error', expectedApiError);
  }));

  it('should toggle the leaderboard visibility state from public to private', async(() => {
    component.leaderboardVisibility = {
      state: 'Public',
      icon: 'fa fa-toggle-on green-text',
    };
    const expectedSuccessMsg = 'The phase split was successfully made private';
    spyOn(apiService, 'patchFileUrl').and.returnValue(
      new Observable((observer) => {
        observer.next({ results: [{}] });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.toggleLeaderboardVisibility();
    fixture.detectChanges();
    expect(apiService.patchFileUrl).toHaveBeenCalled();
    expect(component.leaderboardVisibility.state).toEqual('Private');
    expect(component.leaderboardVisibility.icon).toEqual('fa fa-toggle-off grey-text text-darken-1');
    expect(globalService.showToast).toHaveBeenCalledWith('success', expectedSuccessMsg, 5);
  }));

  it('should toggle the leaderboard visibility state from private to public', async(() => {
    component.leaderboardVisibility = {
      state: 'Private',
      icon: 'fa fa-toggle-off grey-text text-darken-1',
    };
    const expectedSuccessMsg = 'The phase split was successfully made public';
    spyOn(apiService, 'patchFileUrl').and.returnValue(
      new Observable((observer) => {
        observer.next({ results: [{}] });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.toggleLeaderboardVisibility();
    fixture.detectChanges();
    expect(apiService.patchFileUrl).toHaveBeenCalled();
    expect(component.leaderboardVisibility.state).toEqual('Public');
    expect(component.leaderboardVisibility.icon).toEqual('fa fa-toggle-on green-text');
    expect(globalService.showToast).toHaveBeenCalledWith('success', expectedSuccessMsg, 5);
  }));

  it('should handle the API error for `toggleLeaderboardVisiblity` method', async(() => {
    const expectedApiError = {
      error: 'Api error',
    };
    spyOn(apiService, 'patchFileUrl').and.returnValue(
      new Observable((observer) => {
        observer.error({ error: expectedApiError.error });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.toggleLeaderboardVisibility();
    fixture.detectChanges();
    expect(apiService.patchFileUrl).toHaveBeenCalled();
    expect(globalService.handleApiError).toHaveBeenCalledWith(expectedApiError, true);
    expect(globalService.showToast).toHaveBeenCalledWith('error', expectedApiError);
  }));

  it('should update leaderboard precision value', async(() => {
    component.leaderboardPrecisionValue = 2;
    const updatedLeaderboardPrecisionValue = 3;
    spyOn(apiService, 'patchUrl').and.returnValue(
      new Observable((observer) => {
        observer.next({ results: [{}] });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.updateLeaderboardDecimalPrecision(updatedLeaderboardPrecisionValue);
    fixture.detectChanges();
    expect(apiService.patchUrl).toHaveBeenCalled();
    expect(component.leaderboardPrecisionValue).toEqual(updatedLeaderboardPrecisionValue);
    expect(component.plusDisabled).toEqual(false);
    expect(component.minusDisabled).toEqual(false);
  }));

  it('should disable plus button when leaderboard precision value is 20', async(() => {
    component.leaderboardPrecisionValue = 19;
    const updatedLeaderboardPrecisionValue = 20;
    spyOn(apiService, 'patchUrl').and.returnValue(
      new Observable((observer) => {
        observer.next({ results: [{}] });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.updateLeaderboardDecimalPrecision(updatedLeaderboardPrecisionValue);
    fixture.detectChanges();
    expect(apiService.patchUrl).toHaveBeenCalled();
    expect(component.leaderboardPrecisionValue).toEqual(updatedLeaderboardPrecisionValue);
    expect(component.plusDisabled).toEqual(true);
  }));

  it('should disable minus button when leaderboard precision value is 0', async(() => {
    component.leaderboardPrecisionValue = 1;
    const updatedLeaderboardPrecisionValue = 0;
    spyOn(apiService, 'patchUrl').and.returnValue(
      new Observable((observer) => {
        observer.next({ results: [{}] });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.updateLeaderboardDecimalPrecision(updatedLeaderboardPrecisionValue);
    fixture.detectChanges();
    expect(apiService.patchUrl).toHaveBeenCalled();
    expect(component.leaderboardPrecisionValue).toEqual(updatedLeaderboardPrecisionValue);
    expect(component.minusDisabled).toEqual(true);
  }));

  it('should show edit phase modal and successfully edit phase details', () => {
    const updatedPhaseDetails = {
      allowed_submission_file_types: ".json",
      description: "<p>phase description</p>",
      end_date: "2099-12-12T14:29:29.350Z",
      max_concurrent_submissions_allowed: 3,
      max_submissions: 100000,
      max_submissions_per_day: 100000,
      max_submissions_per_month: 100000,
      name: "Phase Name",
      start_date: "2021-04-21T14:29:29.350Z"
    };
    const expectedSuccessMsg = 'The challenge phase details are successfully updated!';
    spyOn(apiService, 'patchFileUrl').and.returnValue(
      new Observable((observer) => {
        observer.next({ results: [{}] });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.editPhaseDetails();
    expect(globalService.showEditPhaseModal).toHaveBeenCalled();
    component.apiCall(updatedPhaseDetails);
    expect(apiService.patchFileUrl).toHaveBeenCalled();
    expect(globalService.showToast).toHaveBeenCalledWith('success', expectedSuccessMsg, 5);
  });

  it('should handle the API error for `editPhaseDetails` method', () => {
    const updatedPhaseDetails = {
      allowed_submission_file_types: ".json",
      description: "<p>phase description</p>",
      end_date: "2029-12-12T14:29:29.350Z",
      max_concurrent_submissions_allowed: 3,
      max_submissions: 100000,
      max_submissions_per_day: 100000,
      max_submissions_per_month: 100000,
      name: "Phase Name",
      start_date: "2021-04-21T14:29:29.350Z"
    };
    const expectedErrorMsg = {
      error: 'Api error',
    };
    spyOn(apiService, 'patchFileUrl').and.returnValue(
      new Observable((observer) => {
        observer.error({ error: expectedErrorMsg.error });
        observer.complete();
        return { unsubscribe() {} };
      })
    );

    component.editPhaseDetails();
    expect(globalService.showEditPhaseModal).toHaveBeenCalled();
    component.apiCall(updatedPhaseDetails);
    expect(apiService.patchFileUrl).toHaveBeenCalled();
    expect(globalService.showToast).toHaveBeenCalledWith('error', expectedErrorMsg);
  });

});
