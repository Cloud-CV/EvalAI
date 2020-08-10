import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ChallengeevaluationComponent } from './challengeevaluation.component';
import { ChallengeService } from '../../../services/challenge.service';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';
import { HttpClientModule } from '@angular/common/http';
import { RouterTestingModule } from '@angular/router/testing';
import { AuthService } from '../../../services/auth.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { Observable } from 'rxjs';

describe('ChallengeevaluationComponent', () => {
  let component: ChallengeevaluationComponent;
  let fixture: ComponentFixture<ChallengeevaluationComponent>;
  let globalService, apiService;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ChallengeevaluationComponent],
      providers: [ChallengeService, ApiService, GlobalService, AuthService, EndpointsService],
      imports: [RouterTestingModule, HttpClientModule],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChallengeevaluationComponent);
    globalService = TestBed.get(GlobalService);
    apiService = TestBed.get(ApiService);
    component = fixture.componentInstance;

    spyOn(globalService, 'showModal');
    spyOn(globalService, 'showToast');
    spyOn(component, 'updateView');
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('global variables', () => {
    expect(component.isChallengeHost).toBeFalsy();
  });

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

  it('should show modal and successfully edit evaluation script', () => {
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
});
