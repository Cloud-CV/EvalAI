import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { GlobalService } from '../../../services/global.service';
import { AuthService } from '../../../services/auth.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { RouterTestingModule } from '@angular/router/testing';
import { HeaderStaticComponent } from './header-static.component';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../../services/api.service';
import { HttpClientModule } from '@angular/common/http';

describe('HeaderStaticComponent', () => {
  let component: HeaderStaticComponent;
  let fixture: ComponentFixture<HeaderStaticComponent>;
  const fakeActivatedRoute = {
    snapshot: { data: { } }
  } as ActivatedRoute;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ HeaderStaticComponent ],
      providers: [ GlobalService,
        AuthService,
        ApiService,
        EndpointsService ],
      imports: [ RouterTestingModule, HttpClientModule ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(HeaderStaticComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });
  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
