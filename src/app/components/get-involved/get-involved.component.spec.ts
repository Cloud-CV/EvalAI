import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { GlobalService } from '../../services/global.service';
import { AuthService } from '../../services/auth.service';
import { EndpointsService } from '../../services/endpoints.service';
import { GetInvolvedComponent } from './get-involved.component';
import { HeaderStaticComponent } from '../../components/nav/header-static/header-static.component';
import { ActivatedRoute, Router } from '@angular/router';
import { FooterComponent } from '../../components/nav/footer/footer.component';
import { RouterTestingModule } from '@angular/router/testing';
import { ApiService } from '../../services/api.service';
import { HttpClientModule } from '@angular/common/http';

describe('GetInvolvedComponent', () => {
  let component: GetInvolvedComponent;
  let fixture: ComponentFixture<GetInvolvedComponent>;
  const fakeActivatedRoute = {
    snapshot: { data: { } }
  } as ActivatedRoute;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ GetInvolvedComponent, HeaderStaticComponent, FooterComponent ],
      providers: [
        GlobalService,
        AuthService,
        ApiService,
        {provide: ActivatedRoute, useValue: fakeActivatedRoute},
        {provide: Router, useClass: class { navigate = jasmine.createSpy('navigate'); }},
        EndpointsService
      ],
      imports: [ RouterTestingModule, HttpClientModule ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GetInvolvedComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
