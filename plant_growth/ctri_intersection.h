/*
  In this file is the code of the algorithm described in:

  "A fast triangle to triangle intersection test for collision detection"
    Oren Tropp, Ayellet Tal, Ilan Shimshoni
       Computer Animation and Virtual Worlds 17(5) 2006, pp 527-535.

    You are free to use the code but cite the paper.


    The following code tests for 3D triangle triangle intersection.
     Main procedures:

    int tr_tri_intersect3D (double *C1, double *P1, double *P2,
         double *D1, double *Q1, double *Q2);

    int coplanar_tri_tri(double N[3],double V0[3],double V1[3],double V2[3],
                     double U0[3],double U1[3],double U2[3]);


  tr_tri_intersect3D - C1 is a vertex of triangle A. P1,P2 are the two edges originating from this vertex.
    D1 is a vertex of triangle B. P1,P2 are the two edges originating from this vertex.
    Returns zero for disjoint triangles and non-zero for intersection.

  coplanar_tri_tri - This procedure for testing coplanar triangles for intersection is
  taken from Tomas Moller's algorithm.
  See article "A Fast Triangle-Triangle Intersection Test",
  Journal of Graphics Tools, 2(2), 1997
  V1,V2,V3 are vertices of one triangle with normal N. U1,U2,U3 are vertices of the other
  triangle.

*/
#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>
#include <math.h>
#include <memory.h>
#include <time.h>
#include <stdbool.h>
#ifndef UNIX
#define drand48() (rand()*1.0/RAND_MAX)
#endif



int coplanar_tri_tri(double N[3],double V0[3],double V1[3],double V2[3],
                     double U0[3],double U1[3],double U2[3]);

// some vector macros
#define CROSS(dest,v1,v2)                       \
               dest[0]=v1[1]*v2[2]-v1[2]*v2[1]; \
               dest[1]=v1[2]*v2[0]-v1[0]*v2[2]; \
               dest[2]=v1[0]*v2[1]-v1[1]*v2[0];



#define   sVpsV_2( Vr, s1,  V1,s2, V2);\
    {\
  Vr[0] = s1*V1[0] + s2*V2[0];\
  Vr[1] = s1*V1[1] + s2*V2[1];\
}\

#define myVpV(g,v2,v1);\
{\
    g[0] = v2[0]+v1[0];\
    g[1] = v2[1]+v1[1];\
    g[2] = v2[2]+v1[2];\
    }\

  #define myVmV(g,v2,v1);\
{\
    g[0] = v2[0]-v1[0];\
    g[1] = v2[1]-v1[1];\
    g[2] = v2[2]-v1[2];\
    }\

// 2D intersection of segment and triangle.
#define seg_collide3( q, r)\
{\
    p1[0]=SF*P1[0];\
    p1[1]=SF*P1[1];\
    p2[0]=SF*P2[0];\
    p2[1]=SF*P2[1];\
    det1 = p1[0]*q[1]-q[0]*p1[1];\
    gama1 = (p1[0]*r[1]-r[0]*p1[1])*det1;\
    alpha1 = (r[0]*q[1] - q[0]*r[1])*det1;\
    alpha1_legal = (alpha1>=0) && (alpha1<=(det1*det1)  && (det1!=0));\
    det2 = p2[0]*q[1] - q[0]*p2[1];\
    alpha2 = (r[0]*q[1] - q[0]*r[1]) *det2;\
    gama2 = (p2[0]*r[1] - r[0]*p2[1]) * det2;\
    alpha2_legal = (alpha2>=0) && (alpha2<=(det2*det2) && (det2 !=0));\
    det3=det2-det1;\
    gama3=((p2[0]-p1[0])*(r[1]-p1[1]) - (r[0]-p1[0])*(p2[1]-p1[1]))*det3;\
    if (alpha1_legal)\
    {\
        if (alpha2_legal)\
        {\
            if ( ((gama1<=0) && (gama1>=-(det1*det1))) || ((gama2<=0) && (gama2>=-(det2*det2))) || (gama1*gama2<0)) return 12;\
        }\
        else\
        {\
            if ( ((gama1<=0) && (gama1>=-(det1*det1))) || ((gama3<=0) && (gama3>=-(det3*det3))) || (gama1*gama3<0)) return 13;\
            }\
    }\
    else\
    if (alpha2_legal)\
    {\
        if ( ((gama2<=0) && (gama2>=-(det2*det2))) || ((gama3<=0) && (gama3>=-(det3*det3))) || (gama2*gama3<0)) return 23;\
        }\
    return 0;\
    }




//main procedure

int tr_tri_intersect3D (double *C1, double *P1, double *P2,
         double *D1, double *Q1, double *Q2)
{
    double  t[3],p1[3], p2[3],r[3],r4[3];
    double beta1, beta2, beta3;
    double gama1, gama2, gama3;
    double det1, det2, det3;
    double dp0, dp1, dp2;
    double dq1,dq2,dq3,dr, dr3;
    double alpha1, alpha2;
    bool alpha1_legal, alpha2_legal;
    double  SF;
    bool beta1_legal, beta2_legal;

    myVmV(r,D1,C1);
    // determinant computation
    dp0 = P1[1]*P2[2]-P2[1]*P1[2];
    dp1 = P1[0]*P2[2]-P2[0]*P1[2];
    dp2 = P1[0]*P2[1]-P2[0]*P1[1];
    dq1 = Q1[0]*dp0 - Q1[1]*dp1 + Q1[2]*dp2;
    dq2 = Q2[0]*dp0 - Q2[1]*dp1 + Q2[2]*dp2;
    dr  = -r[0]*dp0  + r[1]*dp1  - r[2]*dp2;



    beta1 = dr*dq2;  // beta1, beta2 are scaled so that beta_i=beta_i*dq1*dq2
    beta2 = dr*dq1;
    beta1_legal = (beta2>=0) && (beta2 <=dq1*dq1) && (dq1 != 0);
    beta2_legal = (beta1>=0) && (beta1 <=dq2*dq2) && (dq2 != 0);

    dq3=dq2-dq1;
    dr3=+dr-dq1;   // actually this is -dr3


    if ((dq1 == 0) && (dq2 == 0))
    {
        if (dr!=0) return 0;  // triangles are on parallel planes
        else
        {                       // triangles are on the same plane
            double C2[3],C3[3],D2[3],D3[3], N1[3];
            // We use the coplanar test of Moller which takes the 6 vertices and 2 normals
            //as input.
            myVpV(C2,C1,P1);
            myVpV(C3,C1,P2);
            myVpV(D2,D1,Q1);
            myVpV(D3,D1,Q2);
            CROSS(N1,P1,P2);
            return coplanar_tri_tri(N1,C1, C2,C3,D1,D2,D3);
        }
    }

    else if (!beta2_legal && !beta1_legal) return 0;// fast reject-all vertices are on
                                                    // the same side of the triangle plane

    else if (beta2_legal && beta1_legal)    //beta1, beta2
    {
        SF = dq1*dq2;
        sVpsV_2(t,beta2,Q2, (-beta1),Q1);
    }

    else if (beta1_legal && !beta2_legal)   //beta1, beta3
    {
        SF = dq1*dq3;
        beta1 =beta1-beta2;   // all betas are multiplied by a positive SF
        beta3 =dr3*dq1;
        sVpsV_2(t,(SF-beta3-beta1),Q1,beta3,Q2);
    }

    else if (beta2_legal && !beta1_legal) //beta2, beta3
    {
        SF = dq2*dq3;
        beta2 =beta1-beta2;   // all betas are multiplied by a positive SF
        beta3 =dr3*dq2;
        sVpsV_2(t,(SF-beta3),Q1,(beta3-beta2),Q2);
        Q1=Q2;
        beta1=beta2;
    }
    sVpsV_2(r4,SF,r,beta1,Q1);
    seg_collide3(t,r4);  // calculates the 2D intersection
    return 0;
}






/* this edge to edge test is based on Franlin Antonio's gem:
   "Faster Line Segment Intersection", in Graphics Gems III,
   pp. 199-202 */
#define FABS(x) (x>=0?x:-x)        /* implement as is fastest on your machine */

#define EDGE_EDGE_TEST(V0,U0,U1)                      \
  Bx=U0[i0]-U1[i0];                                   \
  By=U0[i1]-U1[i1];                                   \
  Cx=V0[i0]-U0[i0];                                   \
  Cy=V0[i1]-U0[i1];                                   \
  f=Ay*Bx-Ax*By;                                      \
  d=By*Cx-Bx*Cy;                                      \
  if((f>0 && d>=0 && d<=f) || (f<0 && d<=0 && d>=f))  \
  {                                                   \
    e=Ax*Cy-Ay*Cx;                                    \
    if(f>0)                                           \
    {                                                 \
      if(e>=0 && e<=f) return 1;                      \
    }                                                 \
    else                                              \
    {                                                 \
      if(e<=0 && e>=f) return 1;                      \
    }                                                 \
  }

#define EDGE_AGAINST_TRI_EDGES(V0,V1,U0,U1,U2) \
{                                              \
  double Ax,Ay,Bx,By,Cx,Cy,e,d,f;               \
  Ax=V1[i0]-V0[i0];                            \
  Ay=V1[i1]-V0[i1];                            \
  /* test edge U0,U1 against V0,V1 */          \
  EDGE_EDGE_TEST(V0,U0,U1);                    \
  /* test edge U1,U2 against V0,V1 */          \
  EDGE_EDGE_TEST(V0,U1,U2);                    \
  /* test edge U2,U1 against V0,V1 */          \
  EDGE_EDGE_TEST(V0,U2,U0);                    \
}

#define POINT_IN_TRI(V0,U0,U1,U2)           \
{                                           \
  double a,b,c,d0,d1,d2;                     \
  /* is T1 completly inside T2? */          \
  /* check if V0 is inside tri(U0,U1,U2) */ \
  a=U1[i1]-U0[i1];                          \
  b=-(U1[i0]-U0[i0]);                       \
  c=-a*U0[i0]-b*U0[i1];                     \
  d0=a*V0[i0]+b*V0[i1]+c;                   \
                                            \
  a=U2[i1]-U1[i1];                          \
  b=-(U2[i0]-U1[i0]);                       \
  c=-a*U1[i0]-b*U1[i1];                     \
  d1=a*V0[i0]+b*V0[i1]+c;                   \
                                            \
  a=U0[i1]-U2[i1];                          \
  b=-(U0[i0]-U2[i0]);                       \
  c=-a*U2[i0]-b*U2[i1];                     \
  d2=a*V0[i0]+b*V0[i1]+c;                   \
  if(d0*d1>0.0)                             \
  {                                         \
    if(d0*d2>0.0) return 1;                 \
  }                                         \
}

//This procedure testing for intersection between coplanar triangles is taken
// from Tomas Moller's
//"A Fast Triangle-Triangle Intersection Test",Journal of Graphics Tools, 2(2), 1997
int coplanar_tri_tri(double N[3],double V0[3],double V1[3],double V2[3],
                     double U0[3],double U1[3],double U2[3])
{
   double A[3];
   short i0,i1;
   /* first project onto an axis-aligned plane, that maximizes the area */
   /* of the triangles, compute indices: i0,i1. */
   A[0]=FABS(N[0]);
   A[1]=FABS(N[1]);
   A[2]=FABS(N[2]);
   if(A[0]>A[1])
   {
      if(A[0]>A[2])
      {
          i0=1;      /* A[0] is greatest */
          i1=2;
      }
      else
      {
          i0=0;      /* A[2] is greatest */
          i1=1;
      }
   }
   else   /* A[0]<=A[1] */
   {
      if(A[2]>A[1])
      {
          i0=0;      /* A[2] is greatest */
          i1=1;
      }
      else
      {
          i0=0;      /* A[1] is greatest */
          i1=2;
      }
    }

    /* test all edges of triangle 1 against the edges of triangle 2 */
    EDGE_AGAINST_TRI_EDGES(V0,V1,U0,U1,U2);
    EDGE_AGAINST_TRI_EDGES(V1,V2,U0,U1,U2);
    EDGE_AGAINST_TRI_EDGES(V2,V0,U0,U1,U2);

    /* finally, test if tri1 is totally contained in tri2 or vice versa */
    POINT_IN_TRI(V0,U0,U1,U2);
    POINT_IN_TRI(U0,V0,V1,V2);

    return 0;
}

/*
This is a simple test engine which runs the triangle to triangle test


  */


#define TEST

#ifdef TEST


double PS[10000][3][3];
double QS[10000][3][3];
double EPS[10000][2][3];
double EQS[10000][2][3];
void main()
{

    int i;
    int j;
    int k;
    int t_1 = clock();
    srand(t_1);
    for(i=0; i<10000; i++){
        for(j=0; j<3; j++){
            for(k=0; k<3; k++){
                PS[i][j][k] = drand48();
                QS[i][j][k] = drand48();
            }
        }
        for(j=0; j<2; j++){
            for(k=0; k<3; k++){
                EPS[i][j][k] = PS[i][j+1][k] - PS[i][0][k];
                EQS[i][j][k] = QS[i][j+1][k] - PS[i][0][k];
            }
        }
    }
    double sum=0;
    int t0 = clock();
    int sums[100]={0};
for(j=0; j<1000; j++)
    for(i=0; i<10000; i++){
        int res = tr_tri_intersect3D(PS[i][0],EPS[i][0],EPS[i][1],
                            QS[j][0],EQS[j][0],EQS[j][1]);
        sums[res]++;
    }
    int t1 = clock();
    printf(" time %d %d\n",t0-t_1,t1-t0);
    for(i=0; i<100; i++)
        if(sums[i]!=0)printf("%d %d\n",i,sums[i]);

}
#endif TEST
