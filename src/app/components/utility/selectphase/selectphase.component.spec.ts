import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SelectphaseComponent } from './selectphase.component';
import { GlobalService } from '../../../services/global.service';
import { ChallengeService } from '../../../services/challenge.service';
import { ApiService } from '../../../services/api.service';
import { AuthService } from '../../../services/auth.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { RouterTestingModule } from '@angular/router/testing';
import { HttpClientModule } from '@angular/common/http';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('SelectphaseComponent', () => {
  let component: SelectphaseComponent;
  let fixture: ComponentFixture<SelectphaseComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SelectphaseComponent ],
      providers: [ GlobalService, ChallengeService, ApiService, AuthService, EndpointsService ],
      imports: [ RouterTestingModule, HttpClientModule ],
      schemas: [ NO_ERRORS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SelectphaseComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
