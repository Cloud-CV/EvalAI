import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ChallengeoverviewComponent } from './challengeoverview.component';
import { ChallengeService } from '../../../services/challenge.service';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';
import { HttpClientModule } from '@angular/common/http';
import { AuthService } from '../../../services/auth.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { Observable } from 'rxjs';

describe('ChallengeoverviewComponent', () => {
  let component: ChallengeoverviewComponent;
  let fixture: ComponentFixture<ChallengeoverviewComponent>;
  let globalService, apiService;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ChallengeoverviewComponent ],
      providers: [ ChallengeService, ApiService, GlobalService, AuthService, EndpointsService ],
      imports: [ HttpClientModule ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChallengeoverviewComponent);
    globalService = TestBed.get(GlobalService);
    apiService = TestBed.get(ApiService);
    component = fixture.componentInstance;

    spyOn(globalService, 'showModal');
    spyOn(globalService, 'showToast');
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('global variables', () => {
    expect(component.isChallengeHost).toBeFalsy();
  });

  it('should show modal and successfully edit the challenge description', () => {
    const updatedDescription = 'Updated challenge description';
    const expectedSuccessMsg = 'The description is successfully updated!';
    spyOn(apiService, 'patchUrl').and.returnValue(new Observable((observer) => {
      observer.next({results: [{}]});
      observer.complete();
      return {unsubscribe() {}};
    }));

    component.editChallengeOverview();
    expect(globalService.showModal).toHaveBeenCalled();
    component.apiCall(updatedDescription);
    expect(apiService.patchUrl).toHaveBeenCalled();
    expect(globalService.showToast).toHaveBeenCalledWith('success', expectedSuccessMsg, 5);
  });

  it('should handle the API error for `editChallengeOverview` method', () => {
    const updatedDescription = 'Updated challenge description';
    const expectedErrorMsg = {
      error: 'Api error'
    };
    spyOn(apiService, 'patchUrl').and.returnValue(new Observable((observer) => {
      observer.error({error: expectedErrorMsg.error});
      observer.complete();
      return {unsubscribe() {}};
    }));

    component.editChallengeOverview();
    expect(globalService.showModal).toHaveBeenCalled();
    component.apiCall(updatedDescription);
    expect(apiService.patchUrl).toHaveBeenCalled();
    expect(globalService.showToast).toHaveBeenCalledWith('error', expectedErrorMsg);
  });
});
