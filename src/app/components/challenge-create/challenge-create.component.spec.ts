import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ChallengeCreateComponent } from './challenge-create.component';
import { HeaderStaticComponent } from '../../components/nav/header-static/header-static.component';
import { FooterComponent } from '../../components/nav/footer/footer.component';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { AuthService } from '../../services/auth.service';
import { EndpointsService } from '../../services/endpoints.service';
import { ApiService } from '../../services/api.service';
import { GlobalService } from '../../services/global.service';
import { ChallengeService } from '../../services/challenge.service';
import { RouterTestingModule } from '@angular/router/testing';
import { HttpClientModule } from '@angular/common/http';

describe('ChallengecreateComponent', () => {
  let component: ChallengeCreateComponent;
  let fixture: ComponentFixture<ChallengeCreateComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ChallengeCreateComponent, HeaderStaticComponent, FooterComponent ],
      schemas: [ NO_ERRORS_SCHEMA ],
      imports: [ RouterTestingModule, HttpClientModule ],
      providers: [ GlobalService, AuthService, ApiService, ChallengeService, EndpointsService ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChallengeCreateComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
