import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { GlobalService } from '../global.service';
import { AuthService } from '../services/auth.service';
import { PrivacyPolicyComponent } from './privacy-policy.component';
import { HeaderStaticComponent } from '../partials/nav/header-static/header-static.component';
import { ActivatedRoute, Router } from '@angular/router';

describe('PrivacyPolicyComponent', () => {
  let component: PrivacyPolicyComponent;
  let fixture: ComponentFixture<PrivacyPolicyComponent>;
  const fakeActivatedRoute = {
    snapshot: { data: { } }
  } as ActivatedRoute;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PrivacyPolicyComponent, HeaderStaticComponent ],
      providers: [
        GlobalService,
        AuthService,
        {provide: ActivatedRoute, useValue: fakeActivatedRoute},
        {provide: Router, useClass: class { navigate = jasmine.createSpy('navigate'); }},
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PrivacyPolicyComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
