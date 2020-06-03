import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ChallengeviewallsubmissionsComponent } from './challengeviewallsubmissions.component';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ChallengeService } from '../../../services/challenge.service';
import { GlobalService } from '../../../services/global.service';
import { AuthService } from '../../../services/auth.service';
import { ApiService } from '../../../services/api.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { WindowService } from '../../../services/window.service';
import { HttpClientModule } from '@angular/common/http';
import { RouterTestingModule } from '@angular/router/testing';
import { MatMenuModule } from '@angular/material/menu';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material';

describe('ChallengeviewallsubmissionsComponent', () => {
  let component: ChallengeviewallsubmissionsComponent;
  let fixture: ComponentFixture<ChallengeviewallsubmissionsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ChallengeviewallsubmissionsComponent ],
      providers: [ ChallengeService, GlobalService, AuthService, ApiService,
        EndpointsService, WindowService ],
      imports: [ HttpClientModule, RouterTestingModule, MatMenuModule, MatIconModule, MatTableModule ],
      schemas: [ NO_ERRORS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChallengeviewallsubmissionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
